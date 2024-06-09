#! /usr/bin/env python3

"""

Keith Gough:

Send dummy data via TCP to a given server/hostname for a given duration.
We keep repeating the data until the duration has expired.

Dummy data is read from a file and sent to the server.
Some example dummy data is provided in the DUMMY_DATA list.

"""

import socket
import logging
import time

LOGGER = logging.getLogger(__name__)

# Connect to the server
ADDRESS = ("127.0.0.1", 12000)
# ADDRESS = ("192.168.1.144", 5000)

FILENAME = "/Users/keithgough/Desktop/ais_data.txt"
SEND_DURATION = 300

DUMMY_DATA = [
    b"!AIVDM,1,1,,B,403Ow3AunWje:r6>:`Hc@u?026Bl,0*3A",
    b"!AIVDM,1,1,,A,14eG;C@011r6mV0Hb9M8CnVL0<0;,0*10",
    b"!AIVDM,1,1,,A,15NM=fP01GJ6U<FHjFtuls8T0L0?,0*5A",
    b"!AIVDM,2,1,9,B,55NM=fP23hmeL@KO37TthUHF0jr0ltu8F22 2220O000006WB0BS@DRCQH0jE,0*0E",
    b"!AIVDM,2,2,9,B,6H888888880,2*50",
    b"!AIVDM,1,1,,A,403Ow3AunWje`r6>:fHc@sw026Bl,0*2B",
]


def read_from_file(filename):
    """Read the NMEA data from a file"""
    with open(filename, mode="r", encoding="utf-8") as file:
        ais_data = file.readlines()
    return ais_data


def connect_and_send(data):
    """Connect to the server socket and send the data"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(ADDRESS)
        while True:
            for msg in data:
                time.sleep(0.1)
                s.send(msg.encode("utf-8"))


def main():
    """Entry point"""

    LOGGER.debug("Reading dummy data from: %s", FILENAME)
    data = read_from_file(filename=FILENAME)
    # data = DUMMY_DATA

    LOGGER.debug("Sending for ")
    LOGGER.debug("Sending dummy data to %s", ADDRESS)
    LOGGER.debug("Sending data for %s seconds", SEND_DURATION)

    end_time = time.time() + SEND_DURATION
    while time < end_time:
        connect_and_send(data)

    LOGGER.debug("All done.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
