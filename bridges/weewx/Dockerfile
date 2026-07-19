FROM felddy/weewx:latest

# Switch to root to install packages
USER root

# Install gettext for envsubst and paho-mqtt for MQTTSubscribe
RUN apt-get update && apt-get install -y gettext-base && rm -rf /var/lib/apt/lists/* && \
    env -u PIP_TARGET /opt/venv/bin/pip install paho-mqtt

# Install weewx-mqtt-subscribe extension
RUN git clone https://github.com/weewx-mqtt/subscribe.git /tmp/subscribe && \
    mkdir -p /home/weewx/bin/user /data/bin/user && \
    cp -r /tmp/subscribe/bin/user/* /home/weewx/bin/user/ && \
    cp -r /tmp/subscribe/bin/user/* /data/bin/user/ && \
    touch /home/weewx/bin/user/__init__.py /home/weewx/bin/user/extensions.py && \
    touch /data/bin/user/__init__.py /data/bin/user/extensions.py && \
    rm -rf /tmp/subscribe

# Add /home/weewx/bin to PYTHONPATH
ENV PYTHONPATH=/home/weewx/bin:$PYTHONPATH

# Copy custom entrypoint script
COPY entrypoint.sh /bridges/weewx/entrypoint.sh
RUN chmod +x /bridges/weewx/entrypoint.sh

# Set custom entrypoint
ENTRYPOINT ["/bridges/weewx/entrypoint.sh"]
