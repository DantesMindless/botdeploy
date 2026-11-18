#!/bin/bash
#
# Discord Music Bot - Oracle Cloud / Ubuntu Setup Script
# Run as root: sudo bash setup.sh
#

set -e

INSTALL_DIR="/opt/discordbot"
SERVICE_USER="discordbot"

echo "=== Discord Music Bot Setup ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: Please run as root (sudo bash setup.sh)"
    exit 1
fi

# Update system
echo "[1/8] Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

# Install dependencies
echo "[2/8] Installing dependencies (FFmpeg, Python, Node.js 22)..."
apt-get install -y -qq python3 python3-pip python3-venv ffmpeg curl ca-certificates gnupg

# Install Node.js 22 (required by yt-dlp for YouTube signature solving)
if ! node --version 2>/dev/null | grep -q "v2[2-9]\|v[3-9]"; then
    echo "[2b/8] Installing Node.js 22..."
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" > /etc/apt/sources.list.d/nodesource.list
    apt-get update -qq
    apt-get install -y -qq nodejs
fi

# Create service user
echo "[3/8] Creating service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --create-home --shell /bin/false "$SERVICE_USER"
fi

# Create installation directory
echo "[4/8] Setting up installation directory..."
mkdir -p "$INSTALL_DIR"

# Copy bot files from cloned repo
echo "[5/8] Copying bot files..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

for f in bot.py lang.py requirements.txt .env.example; do
    if [ -f "$REPO_DIR/$f" ]; then
        cp "$REPO_DIR/$f" "$INSTALL_DIR/"
    fi
done

# Create .env file if it doesn't exist
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env" 2>/dev/null || cat > "$INSTALL_DIR/.env" << 'EOF'
DISCORD_TOKEN=your_token_here
OWNER_ID=0
EOF
    echo ""
    echo ">>> IMPORTANT: Edit /opt/discordbot/.env and add your tokens!"
fi

# Set up Python virtual environment
echo "[6/8] Setting up Python environment..."
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
deactivate

# Create writable runtime files
touch "$INSTALL_DIR/bot.log" "$INSTALL_DIR/bans.json" "$INSTALL_DIR/lang_prefs.json"

# Set permissions
echo "[7/8] Setting permissions..."
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chmod 600 "$INSTALL_DIR/.env"

# Install systemd service
echo "[8/8] Installing systemd service..."
cat > /etc/systemd/system/discordbot.service << 'EOF'
[Unit]
Description=Discord Music Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=discordbot
Group=discordbot
WorkingDirectory=/opt/discordbot
ExecStart=/opt/discordbot/venv/bin/python /opt/discordbot/bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/opt/discordbot /home/discordbot

MemoryMax=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

echo ""
echo "=== Setup Complete ==="
echo ""
echo "NEXT STEPS:"
echo ""
echo "  1. Add your tokens:"
echo "     sudo nano /opt/discordbot/.env"
echo "     -> Set DISCORD_TOKEN and OWNER_ID"
echo ""
echo "  2. (Optional) Upload cookies.txt for age-restricted YouTube:"
echo "     sudo cp cookies.txt /opt/discordbot/"
echo "     sudo chown discordbot:discordbot /opt/discordbot/cookies.txt"
echo ""
echo "  3. Start the bot:"
echo "     sudo systemctl start discordbot"
echo "     sudo systemctl enable discordbot"
echo ""
echo "COMMANDS:"
echo "  Logs:    sudo journalctl -u discordbot -f"
echo "  Status:  sudo systemctl status discordbot"
echo "  Restart: sudo systemctl restart discordbot"
echo ""
