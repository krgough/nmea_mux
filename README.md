# nmea_mux - NMEA Multiplexor

Takes NMEA data from Serial Ports, TCP Sockets or UDP Sockets and Multiplex's that data out via a TCP socket on port 10110 and a UDP Broadcast on port 10110.

- Port 10110 is the standard port for NMEA data
- Navionics can be setup to connect via TCP or UDP and listen to the multiplexed data.

```diagram
VHF AIS NMEA Output via FTDI Cable __              __ NMEA Data on TCP port 10110
                                     \            /
TCP Socket on port 5000 ______________\___ Rpi __/___ NMEA Data on UDP Broadcast port 10110
                                      /          \
UDP Socket on port 10110 ____________/            \__ NMEA Data on Serial/FTDI to VHF (for DSC position)
                                    /
GPS Data via USB Serial ___________/
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
