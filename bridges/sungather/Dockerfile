FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Clone SunGather repository
RUN git clone https://github.com/bohdan-s/SunGather.git /opt/sungather

# Checkout specific version (v0.5.3 has the export bug fix)
WORKDIR /opt/sungather
RUN git checkout v0.5.3

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create config directory
RUN mkdir -p /config /logs

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set working directory to SunGather subdirectory where sungather.py is located
WORKDIR /opt/sungather/SunGather

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
