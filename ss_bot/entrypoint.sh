#!/bin/bash
set -e

# Start virtual display :1
Xvfb :1 -screen 0 1920x1080x24 &

# Start window manager (optional)
fluxbox &

# Start VNC server on display :1
x11vnc -display :1 -forever -nopw -listen 0.0.0.0 &

# Set DISPLAY for GUI apps
export DISPLAY=:1

# Start your bot
exec python3 /app/ss_bot.py
