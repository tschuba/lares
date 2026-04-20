FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Clone SunGather repository
RUN git clone https://github.com/bohdan-s/SunGather.git /opt/sungather

# Use main branch for latest fixes (v0.5.3 tag has wrong version string)
WORKDIR /opt/sungather

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Fix export loading bug - add None check using Python
RUN python3 << 'EOF'
with open('SunGather/sungather.py', 'r') as f:
    content = f.read()
content = content.replace(
    "exports = configfile.get('exports', [])\n    for export in exports:",
    "exports = configfile.get('exports', [])\n    if exports is None:\n        exports = []\n    \n    for export in exports:"
)
with open('SunGather/sungather.py', 'w') as f:
    f.write(content)
EOF

# Create config directory
RUN mkdir -p /config /logs

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set working directory to SunGather subdirectory where sungather.py is located
WORKDIR /opt/sungather/SunGather

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
