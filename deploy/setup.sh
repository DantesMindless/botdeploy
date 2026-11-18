#!/bin/bash
#
# Discord Music Bot - Ubuntu Setup Script
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
echo "[1/7] Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

# Install dependencies
echo "[2/7] Installing dependencies..."
apt-get install -y -qq python3 python3-pip python3-venv ffmpeg nodejs npm curl

# Create service user
echo "[3/7] Creating service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --create-home --shell /bin/false "$SERVICE_USER"
fi

# Create installation directory
echo "[4/7] Setting up installation directory..."
mkdir -p "$INSTALL_DIR"

# Copy bot files — use parent dir's consolidated bot.py if available
echo "[5/7] Copying bot files..."
if [ -f ../bot.py ]; then
    cp ../bot.py "$INSTALL_DIR/"
    cp ../requirements.txt "$INSTALL_DIR/"
elif [ -f bot.py ]; then
    cp bot.py "$INSTALL_DIR/"
    cp requirements.txt "$INSTALL_DIR/"
else
    echo "Error: bot.py not found!"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cat > "$INSTALL_DIR/.env" << 'EOF'
# Discord Bot Token
DISCORD_TOKEN=your_token_here
EOF
    echo ""
    echo ">>> IMPORTANT: Edit /opt/discordbot/.env and add your Discord token!"
fi

# Set up Python virtual environment
echo "[6/7] Setting up Python environment..."
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
deactivate

# Set permissions
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chmod 600 "$INSTALL_DIR/.env"

# Install systemd service
echo "[7/7] Installing systemd service..."
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

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

echo ""
echo "=== Setup Complete ==="
echo ""
echo "REQUIRED STEPS:"
echo ""
echo "  1. Add Discord token:"
echo "     sudo nano /opt/discordbot/.env"
echo ""
echo "  2. Upload cookies.txt from Windows:"
echo "     scp cookies.txt user@server:/opt/discordbot/"
echo "     sudo chown discordbot:discordbot /opt/discordbot/cookies.txt"
echo ""
echo "  3. Start the bot:"
echo "     sudo systemctl start discordbot"
echo "     sudo systemctl enable discordbot"
echo ""
echo "AUTO-SYNC: Use sync_cookies.ps1 on Windows with Task Scheduler"
echo "           to automatically sync cookies every 12 hours."
echo ""
echo "Commands:"
echo "  Logs:    sudo journalctl -u discordbot -f"
echo "  Status:  sudo systemctl status discordbot"
echo "  Restart: sudo systemctl restart discordbot"
echo ""
