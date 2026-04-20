FROM felddy/weewx:latest

# Switch to root to install packages
USER root

# Install gettext for envsubst and paho-mqtt for MQTTSubscribe
RUN apt-get update && apt-get install -y gettext-base python3-pip && rm -rf /var/lib/apt/lists/* && \
    pip install paho-mqtt

# Install weewx-mqtt-subscribe extension
RUN git clone https://github.com/weewx-mqtt/subscribe.git /tmp/subscribe && \
    mkdir -p /home/weewx/bin/user /data/bin/user && \
    cp /tmp/subscribe/bin/user/mqttsubscribe.py /home/weewx/bin/user/ && \
    cp /tmp/subscribe/bin/user/mqttsubscribe.py /data/bin/user/ && \
    rm -rf /tmp/subscribe

# Copy custom entrypoint script
COPY entrypoint.sh /bridges/weewx/entrypoint.sh
RUN chmod +x /bridges/weewx/entrypoint.sh

# Set custom entrypoint
ENTRYPOINT ["/bridges/weewx/entrypoint.sh"]
