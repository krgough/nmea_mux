#! /usr/bin/env python3

""" Send Dummy NMEA data via IP (tcp or UDP) to a given hostname

Keith Gough, 30/04/2022

Send dummy data via TCP to a given server/hostname

"""

import socket
import logging
import time

LOGGER = logging.getLogger(__name__)

# Connect to the server
ADDRESS = ("127.0.0.1", 5000)

DUMMY_DATA = [
    "!AIVDM,1,1,,B,403Ow3AunWje:r6>:`Hc@u?026Bl,0*3A",
    "!AIVDM,1,1,,A,14eG;C@011r6mV0Hb9M8CnVL0<0;,0*10",
    "!AIVDM,1,1,,A,15NM=fP01GJ6U<FHjFtuls8T0L0?,0*5A",
    "!AIVDM,2,1,9,B,55NM=fP23hmeL@KO37TthUHF0jr0ltu8F22 2220O000006WB0BS@DRCQH0jE,0*0E",
    "!AIVDM,2,2,9,B,6H888888880,2*50",
    "!AIVDM,1,1,,A,403Ow3AunWje`r6>:fHc@sw026Bl,0*2B",
]


def send_to_socket(sock, msg):
    """Send the message to the given socket"""
    LOGGER.debug("sending %s", msg)
    sock.send(msg.encode())


def send_dummy_data(data, msg_delay):
    """ Send items from the list every 'delay' seconds """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(ADDRESS)
        for my_data in data:
            time.sleep(msg_delay)
            send_to_socket(s, my_data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    send_dummy_data(data=DUMMY_DATA, msg_delay=0.1)
    LOGGER.debug("All done.")
