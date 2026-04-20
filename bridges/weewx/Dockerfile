FROM felddy/weewx:latest

# Switch to root to install packages
USER root

# Install gettext for envsubst and paho-mqtt for MQTTSubscribe
RUN apt-get update && apt-get install -y gettext-base && rm -rf /var/lib/apt/lists/* && \
    /opt/venv/bin/pip install --target /opt/venv/lib/python3.13/site-packages paho-mqtt

# Install weewx-mqtt-subscribe extension
RUN git clone https://github.com/weewx-mqtt/subscribe.git /tmp/subscribe && \
    mkdir -p /home/weewx/bin/user /data/bin/user && \
    cp -r /tmp/subscribe/bin/user/* /home/weewx/bin/user/ && \
    cp -r /tmp/subscribe/bin/user/* /data/bin/user/ && \
    rm -rf /tmp/subscribe

# Add /home/weewx/bin to PYTHONPATH
ENV PYTHONPATH=/home/weewx/bin:$PYTHONPATH

# Copy custom entrypoint script
COPY entrypoint.sh /bridges/weewx/entrypoint.sh
RUN chmod +x /bridges/weewx/entrypoint.sh

# Set custom entrypoint
ENTRYPOINT ["/bridges/weewx/entrypoint.sh"]
