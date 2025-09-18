FROM python:3.11-slim

# System deps (ffmpeg only if you plan on using it here)
RUN apt-get update && apt-get install -y \
    ffmpeg gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "head_bot.py"]