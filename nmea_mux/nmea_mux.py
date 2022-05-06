#! /usr/bin/env python3

""" NMEA Multiplexor - Keith Gough, 30/04/2022

Listen for NMEA/AIS strings on serial ports or IP sockets and re-transmit
them on either TCP or broadcast using UDP.

Useful guidance here > https://steelkiwi.com/blog/working-tcp-sockets/


"""

import logging
import queue
import socket
import select
import threading
import time

import serial

DEBUG = True

LOGGER = logging.getLogger(__name__)

NMEA_MUX_Q = queue.Queue()
STOP_THREADS = threading.Event()
STOP_THREADS.clear()
THREAD_POOL = []

# Max socket buffer size
BUFFER_SIZE = 1024

INPUT_TCP_PORT = 5000
INPUT_TCP_ADDRESS = ("", INPUT_TCP_PORT)

NMEA_PORT = 10110
NMEA_UDP_MUX = ("255.255.255.255", NMEA_PORT)

NMEA_TCP_MUX = ("", NMEA_PORT)

SERIAL_LISTENERS = [
    # ("/dev/null", 115200),
]

TCP_LISTENERS = [
    INPUT_TCP_ADDRESS,
]

MUX_OUPUTS = [
    # NMEA_UDP_MUX,
    NMEA_TCP_MUX,
]

SERIAL_PORT = "/dev/tty.usbserial-FT9FV3Y3"
SERIAL_PORT_BAUD = 9600

MESSAGE_QUEUES = {}
MAX_QUEUE_SIZE = 3


def open_serial_port(port, baud):
    """Open the given serial port"""
    try:
        ser = serial.Serial(port, baud, timeout=1)
        LOGGER.info("Serial port opened...%s", port)
    except IOError as err:
        LOGGER.error("Error opening port: %s", err)
        return None
    return ser


def stop_threads():
    """Set the stop event and wait for all threads to exit"""
    STOP_THREADS.set()
    for thd in THREAD_POOL:
        thd.join()


def flush_queue(my_queue):
    """Empty the given queue"""
    while my_queue.get(block=False):
        pass


def serial_port_worker(port, baud):
    """Listen for data on a serial port and send it to any mux channels"""
    LOGGER.debug("Starting derial port on %s", port)
    ser = open_serial_port(port=port, baud=baud)
    if ser is None:
        STOP_THREADS.set()

    while not STOP_THREADS.is_set():
        try:
            data = ser.readline()
        except serial.SerialException as err:
            LOGGER.error("Serial port error %s: %s", port, err)
            STOP_THREADS.set()
        else:
            LOGGER.debug("Serial Data: %s", data)
            if data:
                for _, mux in MESSAGE_QUEUES.items():
                    mux.put(data)

    if ser:
        ser.close()

    LOGGER.debug("Exiting serial port listener thread for %s", port)


def udp_worker(addr, mux=False):
    """Send received data to the MUX UDP IP connection"""
    # Create a UDP socket with broadcast address
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        MESSAGE_QUEUES[sock] = queue.Queue(MAX_QUEUE_SIZE)
        LOGGER.debug("UDP socket created %s, mux=%s", addr, mux)

    except OSError as err:
        LOGGER.debug(
            "Unable to start UDP connection %s mux=%s, %s",
            addr, mux, err
        )
        STOP_THREADS.set()

    while not STOP_THREADS.is_set():
        # Pull data from the Q and send it to the socket
        try:
            data = MESSAGE_QUEUES[sock].get(timeout=1)

        except queue.Empty:
            pass

        else:
            LOGGER.debug("Sending to UDP MUX: %s, %s", NMEA_UDP_MUX, data)
            try:
                sock.sendto(data, addr)
            except OSError as err:
                LOGGER.debug(err)

    sock.close()
    del MESSAGE_QUEUES[sock]
    LOGGER.debug("Exiting UDP mux worker on %s", addr)


def open_tcp_socket(addr):
    """Try to open a TCP socket with the given address
    Returns the socket if success
    Return None and set the STOP_THREADS flag is there is an error
    """
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(addr)
        server.listen(5)

    except OSError as err:
        LOGGER.debug(
            "Unable to start TCP connection %s, %s",
            addr, err
        )
        STOP_THREADS.set()

    return server


def remove_sockets_with_errors(socks, exceptional):
    """Remove sockets marked exceptional by select from read/write lists"""
    for my_sock in exceptional:
        LOGGER.debug("%s has an error.", my_sock)
        if my_sock in socks['read']:
            socks['read'].remove(my_sock)
        if my_sock in socks['write']:
            socks['write'].remove(my_sock)
            del MESSAGE_QUEUES[my_sock]
    return socks


def send_data_to_output_sockets(writeable, socks):
    """For each wrieSend """
    for my_sock in writeable:
        # Try to get data from our queue
        if my_sock in MESSAGE_QUEUES:
            try:
                data = MESSAGE_QUEUES[my_sock].get(timeout=1)
            except queue.Empty:
                data = None
            else:
                try:
                    my_sock.sendall(data)
                    LOGGER.debug(
                        "Sending to TCP MUX %s, %s",
                        my_sock, data
                    )
                except IOError as err:
                    LOGGER.error("IOError: %s", err)
                    LOGGER.error("Closing socket %s", my_sock)
                    socks['write'].remove(my_sock)
                    my_sock.close()
                    LOGGER.debug("Deleting Queue for %s", my_sock)
                    del MESSAGE_QUEUES[my_sock]
    return socks


def accept_or_read_from_socket(readable, server, mux, socks):
    """For any readable socket then either:
    If it's a new connection then accept it
    else read data from the socket
    """
    # If we have an incomming connection on the server socket
    # then we accept that connection and add it to the write_list
    # to be used for serving data to.
    for my_sock in readable:
        if my_sock is server:
            conn, out_addr = my_sock.accept()
            # conn.setblocking(0)
            if mux:
                MESSAGE_QUEUES[conn] = queue.Queue(MAX_QUEUE_SIZE)
                socks['write'].append(conn)
            else:
                socks['read'].append(conn)

            LOGGER.debug(
                "Connected via TCP on %s mux=%s, to %s",
                my_sock.getsockname(), mux, out_addr
            )

        else:
            data = my_sock.recv(1024)
            if data:
                LOGGER.debug("%s received on %s", data, my_sock.getsockname())
                for _, msg_q in MESSAGE_QUEUES.items():
                    msg_q.put(data)
            else:
                if my_sock in socks['write']:
                    socks['write'].remove(my_sock)
                    del MESSAGE_QUEUES[my_sock]
                socks['read'].remove(my_sock)
                my_sock.close()

    return socks


def tcp_worker(addr, mux=False):
    """Setup a socket and listen for connections"""
    LOGGER.debug("Starting TCP MUX socket thread")

    server = open_tcp_socket(addr)

    socks = {
        'read': [server],
        'write': [],
        'error': [],
    }

    LOGGER.debug("Waiting for TCP connection to %s", addr)

    while not STOP_THREADS.is_set():
        # Use select to determine if a socket is writeable
        # readable, writeable, exceptional
        # Timeout here allows some sleep time for threads to work.
        readable, writeable, exceptional = select.select(
            socks['read'], socks['write'], socks['error'], 1
        )

        # We are not connected yet so we flush the data
        # flush_queue(data_q)

        # If we have an incomming connection on the server socket
        # then we accept that connection and add it to the write_list
        # to be used for serving data to.
        socks = accept_or_read_from_socket(readable, server, mux, socks)

        # If we have writeable sockets (MUX channels) then send any
        # available data to them
        socks = send_data_to_output_sockets(writeable, socks)

        # Deal with any errors. Not sure what errors trigger this.
        socks = remove_sockets_with_errors(socks, exceptional)

    # On exit close the server socket and any others
    server.close()
    for sock in socks['read'] + socks['write']:
        sock.close()

    LOGGER.debug("Exiting TCP socket thread %s mux=%s", addr, mux)


def main():
    """Main program"""

    # Start the TCP MUX thread handler
    tcp_mux_thread = threading.Thread(
        target=tcp_worker,
        args=(NMEA_TCP_MUX, True)
    )
    tcp_mux_thread.daemon = True  # Kills the thread on main program exit
    tcp_mux_thread.start()
    tcp_mux_thread.name = "tcp_mux_thread"
    THREAD_POOL.append(tcp_mux_thread)

    # Start the TCP Listener thread handler
    tcp_input_thread = threading.Thread(
        target=tcp_worker,
        args=(INPUT_TCP_ADDRESS, False)
    )
    tcp_input_thread.daemon = True
    tcp_input_thread.start()
    tcp_input_thread.name = "tcp_input_thread_" + INPUT_TCP_ADDRESS[0]
    THREAD_POOL.append(tcp_input_thread)

    # Start the UDP MUX thread handler
    udp_mux_thread = threading.Thread(
        target=udp_worker,
        args=(NMEA_UDP_MUX, True)
    )
    udp_mux_thread.daemon = True
    udp_mux_thread.start()
    udp_mux_thread.name = "udp_mux_thread"
    THREAD_POOL.append(udp_mux_thread)

    # Start the serial port handler
    # ser_thread = threading.Thread(
    #     target=serial_port_worker,
    #     args=(SERIAL_PORT, SERIAL_PORT_BAUD)
    # )
    # ser_thread.daemon = True
    # ser_thread.start()
    # ser_thread.name = "serial_port_thread"
    # THREAD_POOL.append(ser_thread)

    if DEBUG:
        time.sleep(300)
        STOP_THREADS.set()

    while not STOP_THREADS.is_set():
        time.sleep(1)

    # If we get here then the stop event is set
    # Wait for all threads to stop
    for thd in THREAD_POOL:
        thd.join()

    LOGGER.debug("All done")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
