#!/bin/bash
#
# Cookie Update Script - Run on Ubuntu server
# Downloads new cookies from a remote location or watches for file changes
#
# Usage:
#   ./update_cookies.sh /path/to/new/cookies.txt
#
# Or set up a cron job to check periodically:
#   0 */6 * * * /opt/discordbot/update_cookies.sh /tmp/cookies.txt 2>&1 | logger -t discordbot-cookies
#

INSTALL_DIR="/opt/discordbot"
COOKIE_FILE="$INSTALL_DIR/cookies.txt"
NEW_COOKIE_FILE="$1"

# Check if new cookie file provided
if [ -z "$NEW_COOKIE_FILE" ]; then
    echo "Usage: $0 /path/to/new/cookies.txt"
    exit 1
fi

# Check if new cookie file exists
if [ ! -f "$NEW_COOKIE_FILE" ]; then
    echo "Error: Cookie file not found: $NEW_COOKIE_FILE"
    exit 1
fi

# Validate cookie file (basic check)
if ! grep -q "youtube.com" "$NEW_COOKIE_FILE"; then
    echo "Error: Cookie file doesn't appear to contain YouTube cookies"
    exit 1
fi

# Backup old cookies
if [ -f "$COOKIE_FILE" ]; then
    cp "$COOKIE_FILE" "$COOKIE_FILE.bak"
    echo "Backed up old cookies to $COOKIE_FILE.bak"
fi

# Copy new cookies
cp "$NEW_COOKIE_FILE" "$COOKIE_FILE"
chown discordbot:discordbot "$COOKIE_FILE"
chmod 600 "$COOKIE_FILE"

echo "Cookies updated successfully!"
echo "Cookie file: $COOKIE_FILE"
echo "Last modified: $(stat -c %y "$COOKIE_FILE")"

# Optionally restart the bot to pick up new cookies immediately
read -p "Restart bot now? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl restart discordbot
    echo "Bot restarted."
fi
