# Use the official Python 3.9 image
FROM python:3.9-slim

# Set environment variables for Raspberry Pi dependencies
ENV PYTHONUNBUFFERED=1

# Install system dependencies (for GPIO, I2C, etc.)
RUN apt-get update && apt-get install -y \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-rpi.gpio \
    python3-smbus \
    i2c-tools \
    git \
    build-essential \
    && apt-get clean

# Install necessary Python libraries
RUN pip install --no-cache-dir \
    adafruit-circuitpython-dht \
    adafruit-circuitpython-ssd1306 \
    adafruit-blinka \
    RPi.GPIO \
    adafruit-ads1x15 \
    adafruit-circuitpython-busdevice \
    adafruit-circuitpython-charlcd \
    dht11

# Set the working directory inside the container
WORKDIR /app

# Copy your project into the container
COPY greenhouse /app

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# Set environment variable for time zone (optional)
ENV TZ=UTC

# Run the Python script when the container starts
CMD ["python3", "/app/database_operations.py"]
