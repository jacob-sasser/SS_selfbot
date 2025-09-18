#!/bin/bash
set -e

# For host X11 access
export XAUTHORITY=/dev/null

# Start the bot (blocking)
exec python3 /app/ss_bot.py