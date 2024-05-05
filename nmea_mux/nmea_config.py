#! /usr/bin/env python3

""" Configuration data for NMEA Multiplexor
"""

INPUT_TCP_PORT = 5000
NMEA_PORT = 10110

NMEA_BUS_BAUD = 4800
NMEA_DEV = "/dev/ttyS0"
# NMEA_PORT = "/dev/tty.usbserial-FT9FV3Y3",

AIS_BAUD = 38400
AIS_DEV = "/dev/ttyS1"

GPS_BAUD = 4800
GPS_DEV = "/dev/ttyUSB0"


TCP_MUX = {
    "type": "TCP",
    "is_mux": True,
    "address": ("localhost", NMEA_PORT),
    "name": "TCP MUX for Navionics"
}

UDP_MUX = {
    "type": "UDP",
    "is_mux": True,
    "address": ("255.255.255.255", NMEA_PORT),
    "name": "UDP MUX for Navionics or debug"
}

SERIAL_MUX = {
    "type": "SERIAL",
    "is_mux": True,
    "address": NMEA_DEV,
    "baud": NMEA_BUS_BAUD,
    "name": "NMEA to instruments and VHF"
}

TCP_LISTEN = {
    "type": "TCP",
    "is_mux": False,
    "address": ("localhost", INPUT_TCP_PORT),
    "name": "TCP MUX for Navionics"
}

GPS_LISTEN = {
    "type": "SERIAL",
    "is_mux": False,
    "address": GPS_DEV,
    "baud": GPS_BAUD,
    "name": "USB GPS"
}

AIS_LISTEN = {
    "type": "SERIAL",
    "is_mux": False,
    "address": AIS_DEV,
    "baud": AIS_BAUD,
    "name": "AIS from VHF"
}

CHANNELS = [
    UDP_MUX,
    # SERIAL_MUX,
    # AIS_LISTEN,
    # GPS_LISTEN,
    TCP_MUX,
    TCP_LISTEN,
]
