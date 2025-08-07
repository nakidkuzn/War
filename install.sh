#!/bin/bash

echo "Installing Video Wall Control Panel..."

# Create user
sudo useradd -r -s /bin/false videowall

# Create directories
sudo mkdir -p /opt/video-wall-control
sudo mkdir -p /opt/video-wall-control/static_content
sudo mkdir -p /opt/video-wall-control/uploads
sudo mkdir -p /opt/video-wall-control/logs

# Copy files
sudo cp -r * /opt/video-wall-control/
sudo chown -R videowall:videowall /opt/video-wall-control

# Create virtual environment
cd /opt/video-wall-control
sudo -u videowall python3 -m venv venv
sudo -u videowall ./venv/bin/pip install -r requirements.txt

# Install systemd service
sudo cp video-wall.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable video-wall
sudo systemctl start video-wall

echo "Installation complete!"
echo "Service status:"
sudo systemctl status video-wall
