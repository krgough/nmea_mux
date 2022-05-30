#! /usr/bin/env python3

# Configration data for NMEA Multiplexor

DEBUG = False
INPUT_TCP_PORT = 5000
NMEA_PORT = 10110

TCP_MUX = {
    "type": "TCP",
    "is_mux": True,
    "address": ("", NMEA_PORT),
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
    # "address": "/dev/ttyS1",
    "address": "/dev/tty.usbserial-FT9FV3Y3",
    "baud": 4800,
    "name": "NMEA to instruments and VHF"
}

TCP_LISTEN = {
    "type": "TCP",
    "is_mux": False,
    "address": ("", INPUT_TCP_PORT),
    "name": "TCP MUX for Navionics"
}

GPS_LISTEN = {
    "type": "SERIAL",
    "is_mux": False,
    "address": "/dev/ttyUSB0",
    "baud": 4800,
    "name": "USB GPS"
}

AIS_LISTEN = {
    "type": "SERIAL",
    "is_mux": False,
    "address": "/dev/ttyS0",
    "baud": 38400,
    "name": "AIS from VHF"
}

CHANNELS = [
    UDP_MUX,
    SERIAL_MUX,
    AIS_LISTEN,
    GPS_LISTEN
]

TEST_CHANNELS = [
    TCP_MUX, TCP_LISTEN
]

if DEBUG:
    for chan in TEST_CHANNELS:
        CHANNELS.append(chan)
