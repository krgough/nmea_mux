#! /usr/bin/env bash

# Create a systemd service file for the secure tunnel manager with correct path names
path=$(pwd)
cmd="ExecStart=$path/.venv/bin/python3 $path/nmea_mux/nmea_mux2.py"
echo $cmd
sed 's,.*ExecStart=.*,'"${cmd}," files/nmea_mux.service.template > files/nmea_mux.service

# Install dependencies
echo "Creating .venv"
python3 -m venv .venv
echo "Activating venv"
. .venv/bin/activate
echo "Installing dependencies from requirements.txt"
python3 -m pip install -q -r requirements.txt 

# Setup secure tunnel manager so it starts as a systemd service
echo "Setting up secure tunnel service..."
sudo mv files/nmea_mux.service /etc/systemd/system/
sudo systemctl enable nmea_mux.service
sudo systemctl start nmea_mux.service
sudo systemctl status nmea_mux.service
