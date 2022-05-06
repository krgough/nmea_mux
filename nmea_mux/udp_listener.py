#! /usr/bin/env python3

""" UDP Listener - Keith Gough, 30/04/2022

Listen to messages sent to the broadcast UDP address

"""

import socket
import logging

LOGGER = logging.getLogger(__name__)

# Address
NMEA_PORT = 10110
ADDRESS = ("", NMEA_PORT)
BUFFER_SIZE = 1024


def listen_for_data():
    """ Listen to UDP data on the broadcast address """
    # Create a UDP socket with broadcast address
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(ADDRESS)
        LOGGER.debug("Listening to UDP on %s", ADDRESS)

        while True:
            try:
                data, addr = s.recvfrom(BUFFER_SIZE)
                LOGGER.debug(data)
            except socket.timeout:
                LOGGER.debug("Socket Timeout")
                data = None


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    listen_for_data()
