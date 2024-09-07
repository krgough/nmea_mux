# nmea_mux - NMEA Multiplexor

Takes NMEA data from Serial Ports, TCP Sockets or UDP Sockets and Multiplex's that data out on any combination of TCP/UDP sockets or Serial Ports

- Port 10110 is the standard port for NMEA data
- Navionics can be setup to connect via TCP or UDP and listen to the multiplexed data.

## Typical Configuation

```diagram
                                                __ NMEA Data on UART to VHF (for DSC position)
VHF AIS NMEA Output via UART _                /   and to Instruments (Position, SOG etc)
                               \___ PC/Rpi __/  
GPS Data via USB Serial  ______/             \
                                              \__ NMEA Data on UDP socket port 10110 (Navionics)

```

## All supported

```diagram
NMEA on UART _____________                   _ NMEA Data on TCP socket
                           \               /
NMEA on TCP Socket _________\___ PC/Rpi __/___ NMEA Data on UDP socket
                            /             \
NMEA on UDP Socket ________/               \__ NMEA Data on Serial/FTDI
                          /
GPS Data via USB Serial _/
```

## For testing

Listen to the mux outputs using nc as follows:

For UDP Mux broadcasts on port 10110:

```bash
nc -klu 10110

-l = listen   
-u = udp   
-k = Keep listening (otherwise it stops after first received line)  
```

For TCP mux, listen to port 10110
On MacOS you may have to use `127.0.0.1` rather than `localhost`

```bash
nc localhost 10110
nc 127.0.0.1 10110
```

Test data can be injected using the TCP socket on port 5000.

```bash
nc localhost 5000
nc 127.0.0.1 5000
```
