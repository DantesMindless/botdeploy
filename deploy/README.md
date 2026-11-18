# Discord Music Bot - Deployment Guide

## Deployment Options

### Option A: Railway (Recommended — Easiest)

1. Push your code to a GitHub repo
2. Go to [railway.app](https://railway.app), create a new project from your repo
3. Add your environment variable: `DISCORD_TOKEN=your_token_here`
4. Railway auto-detects the Dockerfile and deploys

**Cost:** ~$5/month (free trial available)

### Option B: Docker on Any VPS

Works on DigitalOcean, Hetzner, Linode, Oracle Cloud (free tier), etc.

```bash
# Clone your repo on the server
git clone https://github.com/youruser/DiscordBot.git
cd DiscordBot

# Create .env
cp .env.example .env
nano .env  # Add your DISCORD_TOKEN

# (Optional) Add cookies.txt for age-restricted content
scp cookies.txt user@server:~/DiscordBot/

# Start
docker compose up -d

# View logs
docker compose logs -f

# Restart after updates
docker compose down && docker compose up -d --build
```

### Option C: Systemd on Ubuntu VPS (No Docker)

```bash
# Upload files to server
scp bot.py requirements.txt .env user@server:/tmp/

# Run the setup script
cd deploy
sudo bash setup.sh

# Configure
sudo nano /opt/discordbot/.env    # Add DISCORD_TOKEN
sudo cp /tmp/cookies.txt /opt/discordbot/  # Optional

# Start
sudo systemctl start discordbot
sudo systemctl enable discordbot  # Auto-start on boot
```

**Management commands:**

| Action | Command |
|--------|---------|
| Start | `sudo systemctl start discordbot` |
| Stop | `sudo systemctl stop discordbot` |
| Restart | `sudo systemctl restart discordbot` |
| Status | `sudo systemctl status discordbot` |
| Logs | `sudo journalctl -u discordbot -f` |

---

## Cookie Management (Optional)

Cookies are needed for age-restricted YouTube content. Without them, most videos still work via the `android_vr` client bypass.

### Export Cookies (on your Windows PC)

```bash
pip install browser-cookie3
python deploy/export_cookies.py
```

### Upload to Server

```bash
scp cookies.txt user@server:/opt/discordbot/
ssh user@server 'sudo chown discordbot:discordbot /opt/discordbot/cookies.txt'
sudo systemctl restart discordbot
```

Cookies expire periodically — refresh every 2-4 weeks.

---

## Security Notes

- **Never commit `.env` or `cookies.txt`** — both are in `.gitignore`
- The bot runs as a non-root user (`discordbot`) with limited permissions
- systemd hardening: `NoNewPrivileges`, `ProtectSystem=strict`, `PrivateTmp`
- Resource limits: 512MB RAM, 50% CPU max
- Error messages sent to Discord are sanitized (no file paths or stack traces)

---

## Troubleshooting

### No audio / FFmpeg errors
```bash
ffmpeg -version          # Verify installed
sudo apt install ffmpeg  # Install if missing
```

### YouTube playback issues
```bash
# Update yt-dlp (do this regularly!)
pip install -U yt-dlp

# Check logs
sudo journalctl -u discordbot -n 50
```

### Voice connection 4017 errors
Ensure discord.py >= 2.7.0:
```bash
pip show discord.py
pip install -U "discord.py[voice]"
```
