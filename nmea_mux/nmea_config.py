#! /usr/bin/env python3

""" Configuration data for NMEA Multiplexor
"""

INPUT_TCP_PORT = 12000
NMEA_PORT = 10110

NMEA_BUS_BAUD = 4800
NMEA_DEV = "/dev/ttyS0"
# NMEA_DEV = "/dev/tty.usbserial-FT9FV3Y3",

AIS_BAUD = 38400
AIS_DEV = "/dev/ttyS1"

GPS_BAUD = 4800
GPS_DEV = "/dev/ttyUSB0"

ALL_NICS = "0.0.0.0"
PHONE_IP = "KeithS22"
PHONE_IP = "10.167.9.84"
PHONE_IP = "192.168.100.229"
ORAC_HOSTNAME = "orac.local"

TCP_NAVIONICS = {
    "type": "TCP",
    "is_mux": True,
    "address": (ALL_NICS, NMEA_PORT),
    "name": "TCP to Navionics"
}

UDP_NAVIONICS = {
    "type": "UDP",
    "is_mux": True,
    "address": (ALL_NICS, NMEA_PORT),  # We don't really car about this for UDP
    "send_to": (PHONE_IP, NMEA_PORT),
    "name": "UDP to Navionics"
}

UART_MUX = {
    "type": "SERIAL",
    "is_mux": True,
    "port": NMEA_DEV,
    "baud": NMEA_BUS_BAUD,
    "name": "UART MUX",
    "address": "/dev/ttyS0",
    # "address": "/dev/tty.usbserial-FT9FV3Y3",
}

TCP_LISTEN = {
    "type": "TCP",
    "is_mux": False,
    "address": (ALL_NICS, INPUT_TCP_PORT),
    "name": "TCP Input"
}

UART_GPS_LISTEN = {
    "type": "SERIAL",
    "is_mux": False,
    "port": GPS_DEV,
    "baud": GPS_BAUD,
    "name": "USB GPS"
}

UART_AIS_LISTEN = {
    "type": "SERIAL",
    "is_mux": False,
    "port": AIS_DEV,
    "baud": AIS_BAUD,
    "name": "AIS from VHF"
}

CHANNELS = [
    # SERIAL_MUX,
    UART_AIS_LISTEN,
    UART_GPS_LISTEN,
    UART_MUX,
    #TCP_LISTEN,
    #TCP_NAVIONICS,
    UDP_NAVIONICS
]
