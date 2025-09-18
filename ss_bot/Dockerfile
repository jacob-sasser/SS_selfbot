# Base image
FROM debian:bookworm-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    firefox-esr \
    wget \
    curl \
    tar \
    pulseaudio \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    libx11-xcb1 \
    libnss3 \
    libasound2 \
    x11-utils \
    python3 python3-pip python3-tk python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set geckodriver version (change if a newer stable release is needed)


# Install geckodriver
ENV GECKO_VERSION=v0.36.0
RUN wget https://github.com/mozilla/geckodriver/releases/download/$GECKO_VERSION/geckodriver-$GECKO_VERSION-linux64.tar.gz && \
    tar -xvzf geckodriver-$GECKO_VERSION-linux64.tar.gz && \
    mv geckodriver /usr/local/bin/ && \
    rm geckodriver-$GECKO_VERSION-linux64.tar.gz

# Upgrade pip
RUN python3 -m pip install --upgrade pip --break-system-packages

# Install Python packages
RUN pip3 install --break-system-packages selenium redis

# Set working directory
WORKDIR /app

# Copy bot script and entrypoint
COPY ss_bot.py /app/ss_bot.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose X11 if needed
ENV DISPLAY=:0

# Mount your persistent Firefox profile (use docker run -v)
# Example: docker run -v /home/jacob/.mozilla/firefox/discord-bot-profile:/app/firefox-profile

# Run entrypoint
ENTRYPOINT ["/entrypoint.sh"]
