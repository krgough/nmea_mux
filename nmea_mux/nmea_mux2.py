#! /usr/bin/env python3
"""
NMEA Multiplexer

This is a version based on socketserver which

Some socketserver help here:
https://pymotw.com/2/SocketServer/
https://docs.python.org/3/library/socketserver.html#socketserver.BaseServer.service_actions

Navionics uses web sockets for AIS data input as follows:

TCP: App connects to a TCP socket on the given address and port and listens for incoming data.
In this case we have to tell the app the IP address of the device running the nmea_mux app.

UDP: App listens on it's own IP on a given port for incoming data.  In the app we must specify
the IP address of the device running the app or address 0.0.0.0.  In this case we have to tell
the nmea_app the address of the device running the Navionics app.  This is possibly simplet as
we are likely using the mobile as a hotspot which has a known fixed ip address.

UDP Listener is a UDP "server".  It listens for incoming UDP messages and sends them to the mux queue.
If we wanted to reply to the client we must extract their address/port from the socket data and send
the response that address/port.  Navionics implements a UDP listener so we can send data to that socket
using a UDP client.

We can also implement UDP listeners as an input port (e.g. for debug)

"""
import logging
import socketserver

import threading
import time
from queue import Queue

import nmea_config as cfg
import pyais
import serial


MAX_Q_SIZE = 100
DATA_QUEUE = Queue(maxsize=MAX_Q_SIZE)
FILTERED_QUEUE = Queue(maxsize=MAX_Q_SIZE)
THREAD_POOL = []
STOP_THREADS = threading.Event()
STOP_THREADS.clear()

LOGGER = logging.getLogger(__name__)


class TCPServer(socketserver.TCPServer):
    """TCP Server socket.  Use is_mux to set the server as a multiplexer or not.
    is_mux = False for input channel
    is_mux = True for output(mux) channel
    """
    def __init__(self, server_address, tcp_handler, channel_name, is_mux=False):
        """Initialise the handler
        We default to an input channel set is_mux to True for a mux/output channel
        """
        self.mux_queue = Queue(maxsize=MAX_Q_SIZE)
        self.name = channel_name
        self.address = server_address
        self.is_mux = is_mux
        super().__init__(server_address, tcp_handler)
        self.start_thread()

    def start_thread(self):
        """Start a thread to operate this socket"""
        server_thread = threading.Thread(target=self.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        LOGGER.debug("Starting TCP Server: %s, %s, mux=%s", self.name, self.address, self.is_mux)
        server_thread.start()
        return server_thread


class TCPHandler(socketserver.BaseRequestHandler):
    """TCP Socket Handler

    """
    def handle(self):
        """Handle the incoming request"""
        LOGGER.info("%s, Connection from: %s", self.server.name, self.client_address[0])

        while True:
            if self.server.is_mux:
                if not self.server.mux_queue.empty():
                    data = self.server.mux_queue.get()
                    LOGGER.debug("%s: Sending to: %s: %s", self.server.name, self.client_address[0], data)
                    try:
                        self.request.sendall(data)
                    except BrokenPipeError:
                        LOGGER.error("%s: Connection from %s closed", self.server.name, self.client_address[0])
                        break

            else:
                try:
                    data = self.request.recv(1024)
                except BrokenPipeError:
                    LOGGER.error("%s: Connection from %s closed", self.server.name, self.client_address[0])

                if not data:
                    break

                LOGGER.debug(
                    "%s: Received from: %s: %s, timeout=%s",
                    self.server.name,
                    self.client_address[0],
                    data,
                    self.server.socket.gettimeout()
                )
                if DATA_QUEUE.full():
                    LOGGER.error("%s: Data queue full.  Dumping oldest message", self.server.name)
                    DATA_QUEUE.get()
                DATA_QUEUE.put(data)

    def finish(self):
        """Finish the request"""
        LOGGER.info("Finished request from: %s", self.client_address[0])
        self.request.close()


class UDPServer(socketserver.UDPServer):
    """UDP Server socket"""
    def __init__(self, server_address, udp_handler, channel_name, is_mux=False, send_to=None):
        self.mux_queue = Queue(maxsize=MAX_Q_SIZE)
        self.name = channel_name
        self.address = server_address
        self.is_mux = is_mux
        self.send_to = send_to
        super().__init__(server_address, udp_handler)
        self.start_thread()

    def service_actions(self):
        """If this is a mux channel then send any messages in the mux_queue to the socket
        If not mux (i.e. an input channel) then we handle incomming messages in the UDP handler
        """
        while self.is_mux and not self.mux_queue.empty():
            data = self.mux_queue.get()
            LOGGER.debug("%s:Sending to: %s: %s", self.name, self.send_to, data)
            try:
                # self.socket.sendto(data, self.address)
                # self.socket.sendto(data, ("0.0.0.0", 10110))
                # self.socket.sendto(data, ("192.168.240.226", 10110))
                self.socket.sendto(data, self.send_to)
            except (BrokenPipeError, OSError) as err:
                LOGGER.error("%s: Connection error = %s", self.name, err)
                break
            time.sleep(0.1)

    def start_thread(self):
        """Start a thread to operate this socket"""
        server_thread = threading.Thread(target=self.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        LOGGER.debug("Starting UDP Server: %s, %s, mux=%s", self.name, self.address, self.is_mux)
        server_thread.start()
        return server_thread


class UDPHandler(socketserver.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """
    def handle(self):
        if not self.server.is_mux:
            data = self.request[0]
            sock = self.request[1]
            LOGGER.debug("%s: Connection from: %s. %s %s", self.server.name, self.client_address[0], data, sock)
            DATA_QUEUE.put(data)


class UARTServer:
    """Class to handle UART serial connections"""
    def __init__(self, port, baud, channel_name, is_mux=False):
        self.name = channel_name
        self.port = port
        self.baud = baud
        self.is_mux = is_mux
        self.mux_queue = Queue(maxsize=MAX_Q_SIZE)
        self.start_thread()

    def open_serial_port(self):
        """Open the given serial port"""
        try:
            ser = serial.Serial(self.port, self.baud, timeout=1)
            LOGGER.info("Serial port opened...%s", self.port)
        except IOError as err:
            LOGGER.error("Error opening port: %s", err)
            return None
        return ser

    def serial_port_worker(self):
        """Listen for data on a serial port and send it to any mux channels"""
        LOGGER.debug("Starting serial port on %s", self.port)
        ser = self.open_serial_port()
        if not ser:
            return

        while not STOP_THREADS.is_set():

            if self.is_mux:
                # Read any messages on mux queue and send those to the serial port
                if not self.mux_queue.empty():
                    data = self.mux_queue.get()
                    if data:
                        LOGGER.debug("Sending to Serial MUX: %s, %s", self.port, data)
                        ser.write(data + b"\r")

            else:
                # Read from the port and put messages onto the mux queue
                try:
                    data = ser.readline().strip()
                except serial.SerialException as err:
                    LOGGER.error("Serial port error %s: %s", self.port, err)
                    STOP_THREADS.set()
                else:
                    LOGGER.debug("Serial Data: %s", data)
                    if data:
                        DATA_QUEUE.put(data)

        if ser:
            ser.close()

        LOGGER.debug("Exiting serial port listener thread for %s", self.port)

    def start_thread(self):
        """Start the serial port worker thread"""
        ser_thread = threading.Thread(target=self.serial_port_worker)
        ser_thread.daemon = True
        ser_thread.start()
        ser_thread.name = self.name
        THREAD_POOL.append(ser_thread)


def reject_ais(data):
    """Returns true if the message is one we want to filter out

    We currently only filter AIS messages where speed=0 i.e. we want to
    de-clutter the display by ignoring stationary targets.

    """
    try:
        ais = pyais.decode(data).asdict()
        LOGGER.debug("AIS: %s", ais)

        if "speed" in ais and ais["speed"] < 0.5:
            return True

    except (
        pyais.exceptions.UnknownMessageException,
        pyais.exceptions.MissingMultipartMessageException
    ):
        pass

    return False


def main():
    """Entry point"""

    channels = []
    for channel in cfg.CHANNELS:
        if channel["type"] == "TCP":
            server = TCPServer(
                channel["address"],
                TCPHandler,
                channel["name"],
                is_mux=channel["is_mux"]
            )
        elif channel["type"] == "UDP":
            server = UDPServer(
                channel["address"],
                UDPHandler,
                channel["name"],
                is_mux=channel["is_mux"],
                send_to=channel["send_to"]
            )
        elif channel["type"] == "SERIAL":
            server = UARTServer(
                port=channel["port"],
                baud=channel["baud"],
                channel_name=channel["name"],
                is_mux=channel["is_mux"]
            )
        else:
            LOGGER.error("Unknown channel type: %s", channel["type"])
            continue

        THREAD_POOL.append(server)
        channels.append(server)

    # Fill the mux channel queues with incomming data
    max_chans = [chan for chan in channels if chan.is_mux]
    while not STOP_THREADS.is_set():
        # DATA_QUEUE.put(b"!AIVDM,1,1,,B,403Ow3AunWje:r6>:`Hc@u?026Bl,0*3A")
        # This blocks forever until there is data on the DATA_QUEUE to handle
        data = DATA_QUEUE.get()
        if not reject_ais(data):
            for channel in max_chans:
                channel.mux_queue.put(data)

        time.sleep(0.001)

    print("All done.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
