FROM python:3.12-slim

# Install system dependencies: FFmpeg for audio, curl for Node.js setup
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -r -s /bin/false botuser

WORKDIR /app

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot.py lang.py ./

# Create writable files with correct permissions
RUN touch bot.log bans.json lang_prefs.json && \
    chown botuser:botuser bot.log bans.json lang_prefs.json

# Switch to non-root user
USER botuser

CMD ["python", "bot.py"]
