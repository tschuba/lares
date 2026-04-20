FROM felddy/weewx:latest

# Switch to root to install packages
USER root

# Install gettext for envsubst
RUN apt-get update && apt-get install -y gettext-base && rm -rf /var/lib/apt/lists/*

# Install weewx-mqtt-subscribe extension
RUN git clone https://github.com/weewx-mqtt/subscribe.git /tmp/subscribe && \
    cd /tmp/subscribe && \
    python3 install.py && \
    rm -rf /tmp/subscribe

# Copy custom entrypoint script
COPY entrypoint.sh /bridges/weewx/entrypoint.sh
RUN chmod +x /bridges/weewx/entrypoint.sh

# Set custom entrypoint
ENTRYPOINT ["/bridges/weewx/entrypoint.sh"]
