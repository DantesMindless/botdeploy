#!/bin/bash
#
# Health Check Script for Discord Music Bot
# Use with monitoring tools or cron
#
# Exit codes:
#   0 = Healthy
#   1 = Service not running
#   2 = Service running but unhealthy
#

SERVICE="discordbot"
LOG_FILE="/opt/discordbot/bot.log"
MAX_LOG_AGE_MINUTES=5

# Check if service is running
if ! systemctl is-active --quiet "$SERVICE"; then
    echo "CRITICAL: Service $SERVICE is not running"
    exit 1
fi

# Check if log file exists and is being written to
if [ -f "$LOG_FILE" ]; then
    # Check if log was updated recently
    LOG_AGE=$(( ($(date +%s) - $(stat -c %Y "$LOG_FILE")) / 60 ))

    if [ "$LOG_AGE" -gt "$MAX_LOG_AGE_MINUTES" ]; then
        echo "WARNING: Log file hasn't been updated in $LOG_AGE minutes"
        # Don't exit with error - bot might just be idle
    fi

    # Check for recent errors
    RECENT_ERRORS=$(tail -100 "$LOG_FILE" | grep -c "ERROR\|CRITICAL" 2>/dev/null || echo 0)
    if [ "$RECENT_ERRORS" -gt 10 ]; then
        echo "WARNING: $RECENT_ERRORS errors in recent log entries"
    fi
fi

# Check memory usage
MEM_USAGE=$(systemctl show "$SERVICE" --property=MemoryCurrent 2>/dev/null | cut -d= -f2)
if [ -n "$MEM_USAGE" ] && [ "$MEM_USAGE" != "[not set]" ]; then
    MEM_MB=$((MEM_USAGE / 1024 / 1024))
    if [ "$MEM_MB" -gt 450 ]; then
        echo "WARNING: High memory usage: ${MEM_MB}MB"
    fi
fi

# Check cookie file age
COOKIE_FILE="/opt/discordbot/cookies.txt"
if [ -f "$COOKIE_FILE" ]; then
    COOKIE_AGE_DAYS=$(( ($(date +%s) - $(stat -c %Y "$COOKIE_FILE")) / 86400 ))
    if [ "$COOKIE_AGE_DAYS" -gt 30 ]; then
        echo "WARNING: Cookies are $COOKIE_AGE_DAYS days old - consider refreshing"
    fi
else
    echo "INFO: No cookies.txt file - YouTube may rate limit"
fi

echo "OK: Service $SERVICE is healthy"
exit 0
