# Cookie Auto-Sync Script for Windows
# Exports YouTube cookies and uploads to Ubuntu server
#
# Setup:
# 1. Edit the SERVER variables below
# 2. Run once manually to test: powershell -ExecutionPolicy Bypass -File sync_cookies.ps1
# 3. Schedule with Task Scheduler to run every 12 hours
#
# Task Scheduler setup:
#   - Action: Start a program
#   - Program: powershell.exe
#   - Arguments: -ExecutionPolicy Bypass -File "C:\DiscordBot\deploy\sync_cookies.ps1"
#   - Trigger: Daily, repeat every 12 hours

# ============ CONFIGURATION ============
$SERVER_USER = "your_username"
$SERVER_HOST = "your_server_ip"
$SERVER_PATH = "/opt/discordbot/cookies.txt"
$BOT_DIR = "C:\DiscordBot"
# ========================================

Write-Host "=== Cookie Auto-Sync ===" -ForegroundColor Cyan
Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# Change to bot directory
Set-Location $BOT_DIR

# Export cookies using Python
Write-Host "[1/3] Exporting cookies from browser..." -ForegroundColor Yellow
$exportResult = & python -c @"
import browser_cookie3
from datetime import datetime

try:
    cookies = browser_cookie3.firefox(domain_name='.youtube.com')
    yt_cookies = list(cookies)

    with open('cookies.txt', 'w') as f:
        f.write('# Netscape HTTP Cookie File\n')
        f.write(f'# Exported: {datetime.now().isoformat()}\n')
        f.write('# Auto-synced from Windows\n\n')

        seen = set()
        for cookie in yt_cookies:
            key = (cookie.domain, cookie.name)
            if key in seen:
                continue
            seen.add(key)
            f.write(f'{cookie.domain}\t')
            f.write(f"{'TRUE' if cookie.domain.startswith('.') else 'FALSE'}\t")
            f.write(f'{cookie.path}\t')
            f.write(f"{'TRUE' if cookie.secure else 'FALSE'}\t")
            f.write(f"{int(cookie.expires) if cookie.expires else '0'}\t")
            f.write(f'{cookie.name}\t')
            f.write(f'{cookie.value}\n')

    print(f'OK: Exported {len(seen)} cookies')
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
"@ 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to export cookies!" -ForegroundColor Red
    Write-Host $exportResult
    exit 1
}
Write-Host $exportResult -ForegroundColor Green

# Upload to server
Write-Host "[2/3] Uploading to server..." -ForegroundColor Yellow
$scpResult = & scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 `
    "$BOT_DIR\cookies.txt" `
    "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to upload!" -ForegroundColor Red
    Write-Host $scpResult
    exit 1
}
Write-Host "Uploaded successfully" -ForegroundColor Green

# Set permissions and restart bot on server
Write-Host "[3/3] Setting permissions and restarting bot..." -ForegroundColor Yellow
& ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 `
    "${SERVER_USER}@${SERVER_HOST}" `
    "sudo chown discordbot:discordbot $SERVER_PATH && sudo chmod 600 $SERVER_PATH && sudo systemctl restart discordbot" 2>&1

Write-Host ""
Write-Host "=== Sync Complete ===" -ForegroundColor Green
Write-Host "Cookies synced and bot restarted on ${SERVER_HOST}"
