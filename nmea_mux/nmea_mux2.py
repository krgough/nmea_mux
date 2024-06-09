"""
NMEA Multiplexer

This is a version based on socketserver which

Some socketserver help here:
https://pymotw.com/2/SocketServer/
https://docs.python.org/3/library/socketserver.html#socketserver.BaseServer.service_actions


UDP Sockets

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


MAX_Q_SIZE = 100
DATA_QUEUE = Queue(maxsize=MAX_Q_SIZE)
THREAD_POOL = []
STOP_THREADS = threading.Event()
STOP_THREADS.clear()

LOGGER = logging.getLogger(__name__)


class TCPHandler(socketserver.BaseRequestHandler):
    """TCP Socket Handler

    """
    def handle(self):
        """Handle the incoming request"""
        LOGGER.info("%s, Connection from: %s", self.server.name, self.client_address[0])

        while True:
            if self.server.is_mux:
                if not DATA_QUEUE.empty():
                    data = DATA_QUEUE.get()
                    LOGGER.debug("%s:Sending to: %s: %s", self.server.name, self.client_address[0], data)
                    try:
                        self.request.sendall(data)
                    except BrokenPipeError:
                        LOGGER.error("%s:Connection from %s closed", self.server.name, self.client_address[0])
                        break

            else:
                try:
                    data = self.request.recv(1024)
                except BrokenPipeError:
                    LOGGER.error("%s:Connection from %s closed", self.server.name, self.client_address[0])

                if not data:
                    break

                LOGGER.debug("%s:Received from: %s: %s", self.server.name, self.client_address[0], data)
                if DATA_QUEUE.full():
                    LOGGER.error("%s:Data queue full.  Dumping oldest message", self.server.name)
                    DATA_QUEUE.get()
                DATA_QUEUE.put(data)

    def finish(self):
        """Finish the request"""
        LOGGER.info("Finished request from: %s", self.client_address[0])
        self.request.close()


class UDPHandler(socketserver.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """
    def handle(self):
        data = self.request[0]
        sock = self.request[1]
        LOGGER.debug("%s: Connection from: %s. %s %s", self.server.name, self.client_address[0], data, sock)

        DATA_QUEUE.put(data)


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


class UDPServer(socketserver.UDPServer):
    """UDP Server socket"""
    def __init__(self, server_address, udp_handler, channel_name, is_mux=False):
        self.mux_queue = Queue(maxsize=MAX_Q_SIZE)
        self.name = channel_name
        self.address = server_address
        self.is_mux = is_mux
        super().__init__(server_address, udp_handler)
        self.start_thread()

    def service_actions(self):
        """If this is a mux channel then send any messages in the mux_queue to the socket
        If not mux (i.e. an input channel) then we handle incomming messages in the UDP handler
        """
        while self.is_mux and not self.mux_queue.empty():
            data = self.mux_queue.get()
            LOGGER.debug("%s:Sending to: %s: %s", self.name, self.address, data)
            try:
                self.socket.sendto(data, self.address)
            except BrokenPipeError:
                LOGGER.error("%s:Connection from %s closed", self.name, "self.client_address[0]")
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


def main():
    """Entry point"""

    server1 = TCPServer(("", 12000), TCPHandler, "TCP_Input_Server", is_mux=False)
    server2 = TCPServer(("", 10110), TCPHandler, "TCP_Output_Server", is_mux=True)
    server3 = UDPServer(("", 10111), UDPHandler, "UDP_Input_Server", is_mux=False)
    # server3 = UDPServer((host, 10111), UDPHandler, "UDP_Output_Server", is_mux=True)

    channels = [server1, server2, server3]

    # Fill the mux channel queues with incomming data
    while True:
        # DATA_QUEUE.put(b"Keith\n")
        if not DATA_QUEUE.empty():
            data = DATA_QUEUE.get()
            for channel in channels:
                if channel.is_mux:
                    LOGGER.debug("Putting msg on queue: msg=%s, channel=%s", data, channel.name)
                    channel.mux_queue.put(data)
        time.sleep(1)

    print("All done.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
