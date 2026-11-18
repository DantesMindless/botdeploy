# Discord Music Bot

A full-featured Discord music bot with a Spotify-style interactive player, YouTube support, audio filters, and multilingual UI.

## Features

- **Interactive player** — buttons and dropdowns, no commands needed after `//start`
- **YouTube playback** — search, direct links, playlists, age-restricted content (with cookies)
- **Audio filters** — bass boost (3 levels), nightcore, vaporwave
- **Queue management** — add, remove, reorder, shuffle, loop modes (single/queue/shuffle)
- **Multilingual** — English, Ukrainian, Russian with `//lang`
- **AI chat** — optional Claude integration via `//ask`
- **Moderation** — owner-only ban, timeout, restart, shutdown, live logs

## Requirements

- Python 3.12+
- FFmpeg
- Node.js 20+ (required by yt-dlp for YouTube signature solving)
- Discord bot token

## Quick Start

1. **Clone and configure:**
   ```bash
   git clone https://github.com/DantesMindless/botdeploy.git
   cd botdeploy
   cp .env.example .env
   # Edit .env — add your DISCORD_TOKEN and OWNER_ID
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run:**
   ```bash
   python bot.py
   ```

## Docker

```bash
cp .env.example .env
# Edit .env with your tokens
docker compose up -d
```

To enable age-restricted YouTube content, place a `cookies.txt` (Netscape format) in the project root. It gets mounted read-only into the container.

## Commands

### Playback
| Command | Description |
|---|---|
| `//start` | Open the interactive player |
| `//play <song/url>` | Play a song, search query, or playlist |
| `//playtop <song/url>` | Add to the front of the queue |
| `//pause` | Pause playback |
| `//resume` | Resume playback |
| `//stop` | Stop and disconnect |
| `//skip` | Skip current song |
| `//skipto <n>` | Skip to position n in queue |
| `//replay` | Replay the last song |

### Queue
| Command | Description |
|---|---|
| `//queue` | Show the current queue |
| `//search <query>` | Search and pick from results |
| `//shuffle` | Shuffle the queue |
| `//loop <off/single/queue/shuffle>` | Set loop mode |
| `//remove <n>` | Remove song at position n |
| `//swap <a> <b>` | Swap two queue positions |
| `//clear` | Clear the queue |

### Audio
| Command | Description |
|---|---|
| `//volume <0-200>` | Set volume |
| `//bass` | Cycle bass boost (off/light/medium/heavy) |
| `//nightcore` | Toggle nightcore |
| `//vaporwave` | Toggle vaporwave |
| `//filters` | Open filter dropdown |

### Utility
| Command | Description |
|---|---|
| `//lang <en/ua/ru>` | Change bot language |
| `//ask <question>` | Ask the AI assistant |
| `//personality [text]` | View or set AI personality |
| `//ping` | Check latency |
| `//move` | Move bot to your voice channel |
| `//help` | Show all commands |

### Owner Only
| Command | Description |
|---|---|
| `//ban @user` | Ban user from the bot |
| `//unban @user` | Remove ban/timeout |
| `//timeout @user <duration>` | Temporary ban (e.g. `30m`, `2h`, `1d`) |
| `//untimeout @user` | Remove timeout |
| `//restart` | Restart the bot |
| `//shutdown` | Shut down the bot |
| `//log [n]` | DM last n log lines (default 20, max 60) |

## Project Structure

```
bot.py              # Main bot code
lang.py             # Translation strings (en, ua, ru)
requirements.txt    # Python dependencies
.env.example        # Environment variable template
Dockerfile          # Container build
docker-compose.yml  # Container orchestration
cookies.txt         # YouTube cookies (not committed)
bans.json           # Ban/timeout data (not committed)
deploy/             # Server deployment scripts
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | Yes | Discord bot token |
| `OWNER_ID` | Yes | Your Discord user ID (enables admin commands) |
| `ANTHROPIC_API_KEY` | No | Claude API key for `//ask` |
| `ASK_DAILY_LIMIT` | No | Max `//ask` per user per day (default: 20) |
| `AUTO_UPDATE_HOURS` | No | yt-dlp auto-update interval (default: 12) |
