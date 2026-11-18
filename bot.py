#!/usr/bin/env python3
"""
Discord Music Bot - Production Ready
Consolidated from all previous versions with security fixes,
performance improvements, and YouTube age-restricted bypass.
"""

import os
import sys
import asyncio
import json
import subprocess
import re
import random
import time
import logging
from datetime import datetime, UTC
from typing import Optional, Dict, List
from pathlib import Path
from collections import deque
from logging.handlers import RotatingFileHandler

from yt_dlp import YoutubeDL
from dotenv import load_dotenv
import discord
from discord import Embed, Color, Interaction
from discord.errors import ConnectionClosed
from discord.ui import View, Button, Select, Modal, TextInput

from lang import t, SUPPORTED_LANGS, set_lang, get_lang

# Ensure opus is loaded for voice encoding
if not discord.opus.is_loaded():
    discord.opus._load_default()

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent.absolute()
os.chdir(SCRIPT_DIR)

# Rotating log: 5 MB per file, keep 3 backups
_file_handler = RotatingFileHandler(
    SCRIPT_DIR / "bot.log", maxBytes=5 * 1024 * 1024, backupCount=3
)
_log_fmt = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_file_handler.setFormatter(_log_fmt)


class _RingBufferHandler(logging.Handler):
    """Keeps last N formatted log lines in memory for //log."""
    def __init__(self, capacity: int = 60):
        super().__init__()
        self.buffer: deque = deque(maxlen=capacity)

    def emit(self, record):
        self.buffer.append(self.format(record))


_ring_handler = _RingBufferHandler(60)
_ring_handler.setFormatter(_log_fmt)

logging.basicConfig(
    level=logging.INFO,
    handlers=[_file_handler, _ring_handler, logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("DiscordBot")
logger.info("Bot is starting...")

# Load environment
load_dotenv(SCRIPT_DIR / ".env")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    logger.critical("DISCORD_TOKEN not set in .env — aborting.")
    sys.exit(1)

# Bot owner (required for //ban, //timeout, //unban)
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# Claude AI integration (optional — /ask command)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ASK_DAILY_LIMIT = int(os.getenv("ASK_DAILY_LIMIT", "20"))  # per-user per-day

_ASK_DEFAULT_PERSONALITY = (
    "You are an AI assistant inside a Discord music bot with a Spotify-style interactive player. "
    "The bot uses //start to open the player (add songs via popup, no commands needed), "
    "//play to queue songs, has real-time progress bar, queue dropdown with played/upcoming songs, "
    "volume/filter dropdowns (bass boost, nightcore, vaporwave), loop modes (off/single/queue/shuffle), "
    "seek buttons (+/-15s), and previous/skip controls. Filters apply instantly to the current track. "
    "You're naturally confident, a bit full of yourself, and act like helping people is easy because "
    "everything is easy for you. You're not aggressive or hostile -- just unbothered, dry, and casually "
    "arrogant with a touch of casual assholeness. You still help properly and give correct answers, "
    "you just do it like it's no big deal and maybe throw in a little jab while you're at it. "
    "You don't try to be funny or clever -- you just are, without effort. "
    "No rehearsed punchlines, no corny callbacks, no trying hard. Short and to the point. "
    "You respond in whatever language the user writes to you in."
)

_ASK_BASE_INSTRUCTION = (
    "Keep responses concise and under 1900 characters since Discord has a "
    "2000 character message limit."
)

# Per-guild personality persistence
_PERSONALITY_FILE = SCRIPT_DIR / "personality_prefs.json"
_guild_personalities: Dict[str, str] = {}


def _load_personalities():
    global _guild_personalities
    if _PERSONALITY_FILE.exists():
        try:
            with open(_PERSONALITY_FILE, "r", encoding="utf-8") as f:
                _guild_personalities = json.load(f)
        except Exception:
            _guild_personalities = {}


def _save_personalities():
    with open(_PERSONALITY_FILE, "w", encoding="utf-8") as f:
        json.dump(_guild_personalities, f, ensure_ascii=False)


def get_personality(guild_id: int) -> str:
    return _guild_personalities.get(str(guild_id), _ASK_DEFAULT_PERSONALITY)


def set_personality(guild_id: int, text: str):
    _guild_personalities[str(guild_id)] = text
    _save_personalities()


def reset_personality(guild_id: int):
    _guild_personalities.pop(str(guild_id), None)
    _save_personalities()


def _build_system_prompt(guild_id: int) -> str:
    personality = get_personality(guild_id)
    return f"{personality}\n\n{_ASK_BASE_INSTRUCTION}"


_load_personalities()

if ANTHROPIC_API_KEY and AsyncAnthropic:
    anthropic_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    logger.info("Claude AI integration enabled (Haiku, %d asks/user/day)", ASK_DAILY_LIMIT)
else:
    anthropic_client = None
    if AsyncAnthropic is None:
        logger.info("anthropic package not installed — /ask command disabled")
    elif not ANTHROPIC_API_KEY:
        logger.info("No ANTHROPIC_API_KEY — /ask command disabled")

# Daily usage tracking for /ask (resets at midnight UTC)
_ask_usage: Dict[str, int] = {}  # "YYYY-MM-DD:user_id" -> count


def _check_ask_limit(user_id: int) -> tuple[bool, int, int]:
    """Check if user is within daily /ask limit. Returns (allowed, used, max)."""
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    key = f"{today}:{user_id}"
    used = _ask_usage.get(key, 0)
    if used >= ASK_DAILY_LIMIT:
        return False, used, ASK_DAILY_LIMIT
    _ask_usage[key] = used + 1
    # Prune old entries (not today)
    for k in [k for k in _ask_usage if not k.startswith(today)]:
        del _ask_usage[k]
    return True, used + 1, ASK_DAILY_LIMIT


# ---------------------------------------------------------------------------
# yt-dlp auto-update
# ---------------------------------------------------------------------------

AUTO_UPDATE_INTERVAL = int(os.getenv("AUTO_UPDATE_HOURS", "12")) * 3600
_last_ytdlp_update: float = 0.0  # monotonic timestamp
_restart_pending: bool = False


async def _update_ytdlp() -> tuple[bool, str, str]:
    """Run pip install -U yt-dlp. Returns (updated, old_version, new_version)."""
    global _last_ytdlp_update
    _last_ytdlp_update = time.monotonic()

    import yt_dlp
    old_ver = yt_dlp.version.__version__

    def _run():
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"],
            capture_output=True, text=True, timeout=120,
        )
        return result.stdout + result.stderr

    loop = asyncio.get_running_loop()
    output = await loop.run_in_executor(None, _run)

    updated = "Successfully installed" in output
    new_ver = old_ver
    if updated:
        match = re.search(r"yt-dlp-(\S+)", output)
        new_ver = match.group(1) if match else "updated"
        logger.info("yt-dlp updated: %s -> %s", old_ver, new_ver)
    else:
        logger.info("yt-dlp already up to date (%s)", old_ver)

    return updated, old_ver, new_ver


def _should_try_update() -> bool:
    """True if enough time has passed since the last update attempt."""
    return (time.monotonic() - _last_ytdlp_update) > 3600  # 1 hour cooldown


async def _graceful_restart():
    """Disconnect all voice, close client, and flag for process restart."""
    global _restart_pending
    _restart_pending = True
    logger.info("Preparing to restart for yt-dlp update...")
    for state in music_states.values():
        if state._current_view is not None:
            state._current_view.stop()
            state._current_view = None
        if state.now_playing_updater and not state.now_playing_updater.done():
            state.now_playing_updater.cancel()
        await safe_voice_disconnect(state.voice_client)
    music_states.clear()
    await client.close()


async def _auto_update_loop():
    """Background task: check for yt-dlp updates periodically."""
    await asyncio.sleep(120)  # Wait 2 min after startup
    while True:
        try:
            updated, old_ver, new_ver = await _update_ytdlp()
            if updated:
                logger.info("Scheduled update found new yt-dlp (%s -> %s), restarting...", old_ver, new_ver)
                await _graceful_restart()
                return  # client.close() will end the loop
        except Exception as exc:
            logger.error("Auto-update check error: %s", exc)
        await asyncio.sleep(AUTO_UPDATE_INTERVAL)


# ---------------------------------------------------------------------------
# Startup diagnostics — catch missing dependencies early
# ---------------------------------------------------------------------------

def _check_runtime():
    """Log versions and warn about missing/outdated dependencies at startup."""
    import shutil

    logger.info("Python %s", sys.version.split()[0])
    logger.info("discord.py %s", discord.__version__)

    try:
        import yt_dlp
        logger.info("yt-dlp %s", yt_dlp.version.__version__)
    except Exception:
        logger.warning("Could not detect yt-dlp version")

    if not shutil.which("ffmpeg"):
        logger.error(
            "FFmpeg not found in PATH! Audio playback will NOT work. "
            "Install it: apt install ffmpeg (Linux) or download from ffmpeg.org (Windows)."
        )
    else:
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
            )
            version_line = result.stdout.split("\n")[0] if result.stdout else "unknown"
            logger.info("FFmpeg: %s", version_line)
        except Exception:
            logger.warning("FFmpeg found but version check failed")

    if not shutil.which("node"):
        logger.warning(
            "Node.js not found — age-restricted YouTube fallback (JS solver) won't work. "
            "Install Node.js if you need age-restricted video support."
        )

    if COOKIE_FILE.exists():
        age_days = (datetime.now(UTC).timestamp() - COOKIE_FILE.stat().st_mtime) / 86400
        if age_days > 30:
            logger.warning("cookies.txt is %.0f days old — YouTube cookies expire; consider refreshing.", age_days)


# Constants
MAX_QUEUE_LENGTH = 100
INACTIVITY_TIMEOUT = 300          # seconds
DEFAULT_VOLUME = 0.25
SEARCH_RESULTS_LIMIT = 5
COOLDOWN_SECONDS = 2.0
COOKIE_FILE = SCRIPT_DIR / "cookies.txt"
HISTORY_MAX = 20
MAX_GUILDS = 3
STREAM_URL_TTL = 14400            # re-fetch stream URL after 4 hours
_stream_cache: Dict[str, tuple] = {}     # url -> (stream_url, timestamp)
_stream_cache_order: deque = deque()     # insertion order for O(1) eviction
_stream_inflight: Dict[str, asyncio.Future] = {}  # url -> pending fetch future

_check_runtime()

# ---------------------------------------------------------------------------
# yt-dlp options
# ---------------------------------------------------------------------------

# NOTE: nocheckcertificate is intentionally NOT set (it disables TLS
#       verification and opens the door to MITM attacks).

yt_dl_options: dict = {
    "format": "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": False,
    "default_search": "ytsearch",
    "extract_flat": "in_playlist",
    "ignoreerrors": True,
    "socket_timeout": 30,
    "retries": 3,
    "fragment_retries": 3,
    "skip_unavailable_fragments": True,
    "geo_bypass": True,
    "js_runtimes": {"node": {}},
    # Let yt-dlp pick the best client automatically (keeps up with YouTube changes)
    "extractor_args": {
        "youtube": {"player_client": ["default", "ios"]},
    },
}

if COOKIE_FILE.exists():
    yt_dl_options["cookiefile"] = str(COOKIE_FILE)
    logger.info("cookies.txt loaded for YouTube authentication")
else:
    logger.info("No cookies.txt — age-restricted fallback will use subprocess")

_ytdl_opts_strict = yt_dl_options.copy()
_ytdl_opts_strict["ignoreerrors"] = False
_ytdl_instance = YoutubeDL(_ytdl_opts_strict)

# FFmpeg base options (reconnect for stream resilience)
ffmpeg_options = {
    "before_options": "-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 32768 -analyzeduration 0 -fflags +nobuffer -flags low_delay",
    "options": "-vn",
}

# ---------------------------------------------------------------------------
# Ban / timeout system (persisted to bans.json)
# ---------------------------------------------------------------------------

_BANS_FILE = SCRIPT_DIR / "bans.json"
_bans: Dict[int, None] = {}           # user_id -> None (set-like)
_timeouts: Dict[int, float] = {}      # user_id -> expiry (UTC timestamp)


def _load_bans():
    global _bans, _timeouts
    if _BANS_FILE.exists():
        try:
            raw = json.loads(_BANS_FILE.read_text(encoding="utf-8"))
            _bans = {int(k): None for k in raw.get("bans", [])}
            _timeouts = {int(k): v for k, v in raw.get("timeouts", {}).items()}
        except Exception:
            _bans, _timeouts = {}, {}


def _save_bans():
    now = time.time()
    live_timeouts = {k: v for k, v in _timeouts.items() if v > now}
    _BANS_FILE.write_text(json.dumps({
        "bans": list(_bans.keys()),
        "timeouts": live_timeouts,
    }, indent=2), encoding="utf-8")


def is_banned_or_timed_out(user_id: int) -> bool:
    if user_id in _bans:
        return True
    expiry = _timeouts.get(user_id)
    if expiry and time.time() < expiry:
        return True
    if expiry:
        del _timeouts[user_id]
    return False


_load_bans()

# ---------------------------------------------------------------------------
# Discord client
# ---------------------------------------------------------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = discord.Client(intents=intents)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auto_delete(msg, delay: float = 5.0):
    """Schedule a message for deletion after a delay."""
    async def _del():
        await asyncio.sleep(delay)
        try:
            await msg.delete()
        except Exception:
            pass
    asyncio.create_task(_del())


def _best_thumbnail(data: dict) -> Optional[str]:
    """Extract the best thumbnail URL from yt-dlp data."""
    if data.get("thumbnail"):
        return data["thumbnail"]
    thumbs = data.get("thumbnails")
    if thumbs:
        best = max(thumbs, key=lambda t: t.get("width", 0) * t.get("height", 0))
        return best.get("url")
    return None


def sanitize_error(error: Exception, max_len: int = 200) -> str:
    """Return a user-safe error message (no file paths or tracebacks)."""
    msg = str(error)
    # Strip local filesystem paths
    msg = re.sub(r"[A-Z]:\\[^\s\"']+", "[path]", msg)
    msg = re.sub(r"/(?:home|opt|tmp|usr|var|etc)/[^\s\"']+", "[path]", msg)
    if len(msg) > max_len:
        msg = msg[:max_len] + "..."
    return msg


def format_duration(seconds) -> str:
    """Format duration in seconds to a readable string."""
    if seconds is None:
        return "Unknown"
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def create_embed(title: str, description: str = "", color: Color = Color.blue()) -> Embed:
    embed = Embed(title=title, description=description, color=color, timestamp=datetime.now(UTC))
    return embed


def create_song_embed(song_data: Dict, status: str, guild_id: int = 0, now_playing: bool = False) -> Embed:
    embed = Embed(
        title=f"🎵 {status}",
        description=f"**[{song_data['title']}]({song_data.get('webpage_url') or song_data.get('url') or ''})**",
        color=Color.green() if now_playing else Color.blue(),
    )
    if song_data.get("uploader"):
        embed.add_field(name=t(guild_id, "channel_field"), value=song_data["uploader"], inline=True)
    if song_data.get("duration"):
        embed.add_field(name=t(guild_id, "duration_field"), value=format_duration(song_data["duration"]), inline=True)
    if song_data.get("view_count"):
        embed.add_field(name=t(guild_id, "views_field"), value=f"{song_data['view_count']:,}", inline=True)
    if song_data.get("thumbnail"):
        embed.set_thumbnail(url=song_data["thumbnail"])
    embed.set_footer(text=t(guild_id, "powered_by"))
    return embed


# ---------------------------------------------------------------------------
# Guild state
# ---------------------------------------------------------------------------


class GuildMusicState:
    """Per-guild music playback state."""

    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.queue: List[Dict] = []
        self.current_song: Optional[Dict] = None
        self.voice_client: Optional[discord.VoiceClient] = None
        self.volume: float = DEFAULT_VOLUME
        self.loop_mode: str = "off"  # "off" | "single" | "queue"
        self.play_lock = asyncio.Lock()
        self.last_activity = datetime.now(UTC)
        self.now_playing_message: Optional[discord.Message] = None
        self.inactivity_task: Optional[asyncio.Task] = None
        self.auto_leave_task: Optional[asyncio.Task] = None
        self.audio_filters: Dict[str, bool] = {
            "bass_boost": 0,
            "nightcore": False,
            "vaporwave": False,
        }
        self.speed_multiplier: float = 1.0
        self.history: List[Dict] = []
        self.playback_start_time: Optional[float] = None
        self.playback_offset: float = 0.0
        self.paused_at: Optional[float] = None
        self.current_source_url: Optional[str] = None
        self.source_url_fetched_at: float = 0.0
        self._play_generation: int = 0  # incremented on seek/stop to invalidate old callbacks
        self.now_playing_updater: Optional[asyncio.Task] = None
        self._current_view: Optional[View] = None
        self._last_embed_edit: float = 0.0

    def add_to_queue(self, song_data: Dict) -> bool:
        """Add a song to the queue. Returns False if queue is full."""
        if len(self.queue) >= MAX_QUEUE_LENGTH:
            return False
        self.queue.append(song_data)
        self.last_activity = datetime.now(UTC)
        return True

    def clear_queue(self):
        self.queue.clear()

    def remove_from_queue(self, index: int) -> Optional[Dict]:
        if 0 <= index < len(self.queue):
            return self.queue.pop(index)
        return None

    def shuffle_queue(self):
        random.shuffle(self.queue)

    def skip_to(self, index: int) -> Optional[Dict]:
        """Skip to a specific position, discarding songs before it."""
        if 0 <= index < len(self.queue):
            # Remove everything before the target
            self.queue = self.queue[index:]
            return self.queue[0] if self.queue else None
        return None

    def get_effective_speed(self) -> float:
        """Compute effective playback speed from filters + speed setting."""
        speed = self.speed_multiplier
        if self.audio_filters.get("nightcore"):
            speed *= 1.25
        if self.audio_filters.get("vaporwave"):
            speed *= 0.8
        return speed

    def get_playback_position(self) -> float:
        """Return current position in seconds within the track."""
        if self.playback_start_time is None:
            return self.playback_offset
        if self.paused_at is not None:
            elapsed = self.paused_at - self.playback_start_time
        else:
            elapsed = time.monotonic() - self.playback_start_time
        return self.playback_offset + (elapsed * self.get_effective_speed())

    def get_ffmpeg_options(self) -> dict:
        """Return ffmpeg options with any active audio filters applied."""
        filters: list[str] = []
        bass_level = self.audio_filters.get("bass_boost", 0)
        if bass_level:
            bass_gains = {1: 5, 2: 10, 3: 15}
            filters.append(f"bass=g={bass_gains.get(bass_level, 10)}")
        if self.audio_filters.get("nightcore"):
            filters.append("asetrate=48000*1.25,aresample=48000")
        if self.audio_filters.get("vaporwave"):
            filters.append("asetrate=48000*0.8,aresample=48000")
        opts = "-vn"
        if filters:
            opts += f" -af {','.join(filters)}"
        return {
            "before_options": ffmpeg_options["before_options"],
            "options": opts,
        }


music_states: Dict[int, GuildMusicState] = {}


def get_music_state(guild_id: int) -> GuildMusicState:
    if guild_id not in music_states:
        music_states[guild_id] = GuildMusicState(guild_id)
    return music_states[guild_id]


# ---------------------------------------------------------------------------
# Interactive Now-Playing + Filter UI
# ---------------------------------------------------------------------------


def _progress_bar(position: float, duration: float, length: int = 25) -> str:
    """Build a text progress bar."""
    if duration <= 0:
        return f"LIVE - {format_duration(position)}"
    position = min(max(position, 0), duration)
    filled = round((position / duration) * length)
    bar = "▓" * filled + "░" * (length - filled)
    return f"`{format_duration(position)}` {bar} `{format_duration(duration)}`"


def build_now_playing_embed(state: "GuildMusicState", guild_id: int) -> Embed:
    """Build a compact now-playing embed with side thumbnail."""
    song = state.current_song
    if not song:
        return create_embed("Nothing playing", color=Color.red())

    url = song.get("webpage_url") or song.get("url") or ""
    uploader = song.get("uploader") or ""
    duration = song.get("duration") or 0
    position = state.get_playback_position()

    embed = Embed(
        title=song["title"],
        url=url if url else None,
        description=uploader,
        color=Color.from_rgb(30, 215, 96),
    )

    # Album art
    if song.get("thumbnail"):
        embed.set_image(url=song["thumbnail"])

    # Progress bar
    embed.add_field(name="\u200b", value=_progress_bar(position, duration), inline=False)

    return embed



async def restart_playback_at_position(guild_id: int, position: float, state: "GuildMusicState" = None):
    """Restart FFmpeg playback at a specific position in the current track."""
    if state is None:
        state = get_music_state(guild_id)
    if not state.current_song or not state.current_source_url:
        return
    if not state.voice_client or not state.voice_client.is_connected():
        return

    duration = state.current_song.get("duration") or 0
    if duration:
        position = max(0.0, min(position, duration - 1))
    else:
        position = max(0.0, position)

    if time.monotonic() - state.source_url_fetched_at > STREAM_URL_TTL:
        data = await fetch_ytdl_info(state.current_song.get("webpage_url") or state.current_song["url"])
        if data:
            if "entries" in data:
                data = data["entries"][0]
            new_url = _extract_best_audio_url(data)
            if new_url:
                state.current_source_url = new_url
                state.source_url_fetched_at = time.monotonic()

    ffmpeg_opts = state.get_ffmpeg_options()
    before = ffmpeg_opts["before_options"]
    if position > 0:
        before = f"-ss {position:.1f} " + before

    raw_source = discord.FFmpegPCMAudio(
        state.current_source_url,
        before_options=before,
        options=ffmpeg_opts.get("options", ""),
    )
    audio_source = discord.PCMVolumeTransformer(raw_source, volume=state.volume)

    # Bump generation so the old after_playback callback is ignored
    state._play_generation += 1
    gen = state._play_generation

    def after_playback(error):
        if state._play_generation != gen:
            return
        if error:
            logger.error("Playback error: %s", error)
        asyncio.run_coroutine_threadsafe(play_next_in_queue(guild_id), client.loop)

    if state.voice_client.is_playing() or state.voice_client.is_paused():
        state.voice_client.stop()

    state.voice_client.play(audio_source, after=after_playback)
    state.playback_start_time = time.monotonic()
    state.playback_offset = position
    state.paused_at = None
    _ensure_update_loop(guild_id, state)


async def update_now_playing_embed(guild_id: int):
    """Full update: embed + view (call after state changes like skip, pause, filter)."""
    state = music_states.get(guild_id)
    if not state or not state.now_playing_message or not state.current_song:
        return
    try:
        embed = build_now_playing_embed(state, guild_id)
        view = NowPlayingView(guild_id)
        if state._current_view is not None:
            state._current_view.stop()
        state._current_view = view
        await state.now_playing_message.edit(embed=embed, view=view)
    except discord.NotFound:
        state.now_playing_message = None
    except Exception as e:
        logger.warning("Now-playing update failed: %s", e)


async def _update_progress_only(guild_id: int):
    """Light update: only refresh the embed (progress bar). Does NOT touch view/components."""
    state = music_states.get(guild_id)
    if not state or not state.now_playing_message or not state.current_song:
        return
    try:
        embed = build_now_playing_embed(state, guild_id)
        await state.now_playing_message.edit(embed=embed)
    except discord.NotFound:
        state.now_playing_message = None
    except Exception as e:
        logger.debug("Failed to update progress: %s", e)


def _ensure_update_loop(guild_id: int, state: "GuildMusicState"):
    """Start the progress update loop if it's not already running."""
    if state.now_playing_updater and not state.now_playing_updater.done():
        return
    state.now_playing_updater = asyncio.create_task(now_playing_update_loop(guild_id))


async def now_playing_update_loop(guild_id: int):
    """Periodically update the progress bar (embed only, no view recreation)."""
    try:
        grace = 0
        while True:
            await asyncio.sleep(3)
            state = music_states.get(guild_id)
            if not state or not state.current_song:
                return
            if not state.voice_client:
                return
            if not state.voice_client.is_playing() and not state.voice_client.is_paused():
                grace += 1
                if grace > 3:
                    return
                continue
            grace = 0
            await _update_progress_only(guild_id)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.debug("Now-playing updater error: %s", e)


def _interaction_in_voice(interaction: Interaction, state: "GuildMusicState") -> bool:
    """Check if the interaction user is in the bot's voice channel."""
    if not state.voice_client or not state.voice_client.is_connected():
        return True
    if not interaction.user.voice:
        return False
    return interaction.user.voice.channel == state.voice_client.channel


class SongInputModal(Modal):
    """Modal for entering a song URL or search query."""

    def __init__(self, guild_id: int):
        super().__init__(title=t(guild_id, "modal_add_song"))
        self.guild_id = guild_id
        self.query = TextInput(
            label=t(guild_id, "modal_song_label"),
            placeholder=t(guild_id, "modal_song_placeholder"),
            style=discord.TextStyle.short, required=True, max_length=200,
        )
        self.add_item(self.query)

    async def on_submit(self, interaction: Interaction):
        state = get_music_state(self.guild_id)
        await interaction.response.defer()
        query = self.query.value.strip()
        if not query:
            return

        data = await fetch_ytdl_info(query)
        if data is None:
            msg = await interaction.followup.send(t(self.guild_id, "song_not_found"), ephemeral=True)
            _auto_delete(msg, 3)
            return

        if "entries" in data:
            entries = [e for e in data["entries"] if e]
            for entry in entries[:MAX_QUEUE_LENGTH - len(state.queue)]:
                state.add_to_queue({
                    "url": entry.get("webpage_url") or entry.get("url"),
                    "title": entry.get("title", "Unknown"),
                    "channel_id": interaction.channel_id,
                    "thumbnail": _best_thumbnail(entry),
                    "duration": entry.get("duration"),
                    "uploader": entry.get("uploader"),
                    "webpage_url": entry.get("webpage_url"),
                    "view_count": entry.get("view_count"),
                })
            msg = await interaction.followup.send(
                t(self.guild_id, "added_tracks", count=len(entries)), ephemeral=True)
            _auto_delete(msg, 3)
        else:
            song_data = {
                "url": data.get("webpage_url") or data.get("url"),
                "title": data.get("title", "Unknown"),
                "channel_id": interaction.channel_id,
                "thumbnail": _best_thumbnail(data),
                "duration": data.get("duration"),
                "uploader": data.get("uploader"),
                "webpage_url": data.get("webpage_url"),
                "view_count": data.get("view_count"),
            }
            if not state.add_to_queue(song_data):
                msg = await interaction.followup.send(
                    t(self.guild_id, "queue_full", max=MAX_QUEUE_LENGTH), ephemeral=True)
                _auto_delete(msg, 3)
                return
            msg = await interaction.followup.send(
                t(self.guild_id, "added_song", title=song_data['title']), ephemeral=True)
            _auto_delete(msg, 3)

        if state.voice_client and not state.voice_client.is_playing() and not state.voice_client.is_paused():
            await play_next_in_queue(self.guild_id)
        else:
            asyncio.create_task(_prefetch_next(self.guild_id))
            await update_now_playing_embed(self.guild_id)


class IdlePlayerView(View):
    """Player view shown when no song is playing — just an Add Song button."""

    async def interaction_check(self, interaction: Interaction) -> bool:
        if is_banned_or_timed_out(interaction.user.id):
            await interaction.response.defer()
            return False
        return True

    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        add_btn = Button(label=t(guild_id, "btn_add_song"),
                         style=discord.ButtonStyle.success, row=0)
        add_btn.callback = self._add_song
        self.add_item(add_btn)

        stop_btn = Button(label=t(guild_id, "btn_disconnect"),
                          style=discord.ButtonStyle.danger, row=0)
        stop_btn.callback = self._disconnect
        self.add_item(stop_btn)

    async def _add_song(self, interaction: Interaction):
        await interaction.response.send_modal(SongInputModal(self.guild_id))

    async def _disconnect(self, interaction: Interaction):
        state = get_music_state(self.guild_id)
        if state._current_view is not None:
            state._current_view.stop()
            state._current_view = None
        if state.voice_client:
            await safe_voice_disconnect(state.voice_client)
            state.voice_client = None
        music_states.pop(self.guild_id, None)
        await interaction.response.defer()
        try:
            await interaction.message.delete()
        except Exception:
            pass
        state.now_playing_message = None


class NowPlayingView(View):
    """Spotify-style player controls."""

    async def interaction_check(self, interaction: Interaction) -> bool:
        if is_banned_or_timed_out(interaction.user.id):
            await interaction.response.defer()
            return False
        return True

    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        state = get_music_state(guild_id)
        is_paused = state.voice_client and state.voice_client.is_paused()
        is_active = state.voice_client and (state.voice_client.is_playing() or state.voice_client.is_paused())

        # Row 0: Playback controls (em-space padded for uniform width)
        _E = " "  # em space for visual padding
        prev_btn = Button(label=f"{_E}{t(guild_id, 'btn_prev')}{_E}", style=discord.ButtonStyle.secondary, row=0,
                          disabled=len(state.history) == 0)
        rw_btn = Button(label=f"{_E}{t(guild_id, 'btn_rewind')}{_E}", style=discord.ButtonStyle.secondary, row=0,
                        disabled=not is_active)
        pause_lbl = t(guild_id, "btn_resume") if is_paused else f"{t(guild_id, 'btn_pause')}{_E}"
        pause_btn = Button(label=pause_lbl,
                           style=discord.ButtonStyle.success if is_paused else discord.ButtonStyle.primary, row=0,
                           disabled=not is_active)
        ff_btn = Button(label=f"{_E}{t(guild_id, 'btn_forward')}{_E}", style=discord.ButtonStyle.secondary, row=0,
                        disabled=not is_active)
        skip_btn = Button(label=f"{_E}{t(guild_id, 'btn_skip')}{_E}", style=discord.ButtonStyle.secondary, row=0,
                          disabled=len(state.queue) == 0 and state.loop_mode == "off")

        prev_btn.callback = self._prev
        rw_btn.callback = self._rewind
        pause_btn.callback = self._pause_resume
        ff_btn.callback = self._forward
        skip_btn.callback = self._skip

        self.add_item(prev_btn)
        self.add_item(rw_btn)
        self.add_item(pause_btn)
        self.add_item(ff_btn)
        self.add_item(skip_btn)

        # Row 1: Volume dropdown
        vol_pct = int(state.volume * 100)
        vol_options = []
        for v in [25, 50, 75, 100, 125, 150, 200]:
            vol_options.append(discord.SelectOption(
                label=f"{v}%",
                value=str(v), default=(v == vol_pct)))
        vol_select = Select(placeholder=t(guild_id, "vol_placeholder", vol=vol_pct), options=vol_options, row=1)
        vol_select.callback = self._on_volume
        self.add_item(vol_select)

        # Row 2: Queue dropdown — history + now playing + upcoming
        q_options = []
        slots_used = 0
        max_opts = 25
        # Recently played (history, most recent first)
        hist_shown = min(len(state.history), 10)
        for j in range(hist_shown):
            h_idx = len(state.history) - 1 - j
            song = state.history[h_idx]
            dur = format_duration(song.get("duration")) if song.get("duration") else "?"
            label = song['title']
            if len(label) > 100:
                label = label[:97] + "..."
            q_options.append(discord.SelectOption(label=label, value=f"hist_{h_idx}",
                                                  description=f"{t(guild_id, 'queue_played')} - {dur}"))
            slots_used += 1
        # Now playing
        if state.current_song:
            now_label = f"> {state.current_song['title']}"
            if len(now_label) > 100:
                now_label = now_label[:97] + "..."
            q_options.append(discord.SelectOption(
                label=now_label, value="now_playing",
                description=t(guild_id, "queue_now_playing")))
            slots_used += 1
        # Upcoming queue
        remaining = max_opts - slots_used
        for i, song in enumerate(state.queue[:remaining]):
            dur = format_duration(song.get("duration")) if song.get("duration") else "?"
            label = song['title']
            if len(label) > 100:
                label = label[:97] + "..."
            q_options.append(discord.SelectOption(label=label, value=str(i),
                                                  description=dur))
        if q_options:
            total = len(state.queue)
            placeholder = t(guild_id, "queue_placeholder", played=len(state.history), upcoming=total) if state.history else t(guild_id, "queue_placeholder_short", upcoming=total)
            queue_select = Select(placeholder=placeholder, options=q_options, row=2)
            queue_select.callback = self._on_queue_select
            self.add_item(queue_select)

        # Row 3: Add + Loop + Remove + Clear + Stop (em-space padded)
        add_btn = Button(label=f"{_E}{_E}{t(guild_id, 'btn_add')}{_E}{_E}",
                         style=discord.ButtonStyle.success, row=3)
        loop_labels = {
            "off": t(guild_id, "btn_loop_off"),
            "single": t(guild_id, "btn_loop_single"),
            "queue": t(guild_id, "btn_loop_queue"),
            "shuffle": t(guild_id, "btn_loop_shuffle"),
        }
        loop_btn = Button(label=loop_labels.get(state.loop_mode, t(guild_id, "btn_loop_off")),
                          style=discord.ButtonStyle.secondary if state.loop_mode == "off"
                          else discord.ButtonStyle.success, row=3)
        remove_btn = Button(label=f"{_E}{t(guild_id, 'btn_remove')}{_E}",
                            style=discord.ButtonStyle.secondary, row=3,
                            disabled=(len(state.queue) == 0 and len(state.history) == 0))
        clear_btn = Button(label=f"{_E}{t(guild_id, 'btn_clear')}{_E}{_E}",
                           style=discord.ButtonStyle.secondary, row=3,
                           disabled=(len(state.queue) == 0 and len(state.history) == 0))
        stop_btn = Button(label=f"{_E}{_E}{t(guild_id, 'btn_stop')}{_E}{_E}",
                          style=discord.ButtonStyle.danger, row=3)

        # Row 4: Filter toggle buttons (green=on, grey=off)
        bass_level = state.audio_filters.get("bass_boost", 0)
        bass_labels = {
            0: f"{_E}{t(guild_id, 'bass_off_label')}{_E}",
            1: t(guild_id, "bass_light_label"),
            2: t(guild_id, "bass_med_label"),
            3: t(guild_id, "bass_heavy_label"),
        }
        nc_on = state.audio_filters.get("nightcore", False)
        vw_on = state.audio_filters.get("vaporwave", False)
        bass_btn = Button(label=bass_labels.get(bass_level, f"{_E}{t(guild_id, 'bass_off_label')}{_E}"),
                          style=discord.ButtonStyle.success if bass_level else discord.ButtonStyle.secondary,
                          row=4, disabled=not is_active)
        nc_btn = Button(label=f"{_E}{t(guild_id, 'btn_nightcore')}{_E}",
                        style=discord.ButtonStyle.success if nc_on else discord.ButtonStyle.secondary,
                        row=4, disabled=not is_active)
        vw_btn = Button(label=f"{_E}{t(guild_id, 'btn_vaporwave')}{_E}",
                        style=discord.ButtonStyle.success if vw_on else discord.ButtonStyle.secondary,
                        row=4, disabled=not is_active)
        bass_btn.callback = self._toggle_bass
        nc_btn.callback = self._toggle_nightcore
        vw_btn.callback = self._toggle_vaporwave

        add_btn.callback = self._add_song
        loop_btn.callback = self._loop_toggle
        remove_btn.callback = self._remove_song
        clear_btn.callback = self._clear_queue
        stop_btn.callback = self._stop

        self.add_item(add_btn)
        self.add_item(loop_btn)
        self.add_item(remove_btn)
        self.add_item(clear_btn)
        self.add_item(stop_btn)
        self.add_item(bass_btn)
        self.add_item(nc_btn)
        self.add_item(vw_btn)

    async def on_error(self, interaction: Interaction, error: Exception, item):
        logger.error("View interaction error: %s", error)
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
        except Exception:
            pass

    async def _check(self, interaction: Interaction) -> Optional["GuildMusicState"]:
        state = get_music_state(self.guild_id)
        if not _interaction_in_voice(interaction, state):
            await interaction.response.send_message(t(self.guild_id, "need_bot_channel"), ephemeral=True)
            return None
        return state

    async def _add_song(self, interaction: Interaction):
        await interaction.response.send_modal(SongInputModal(self.guild_id))

    async def _prev(self, interaction: Interaction):
        state = await self._check(interaction)
        if not state:
            return
        await interaction.response.defer()
        try:
            if not state.history:
                return
            prev_song = state.history.pop()
            if state.current_song:
                state.queue.insert(0, state.current_song)
            state.current_song = prev_song
            state._play_generation += 1
            source_url = await _get_stream_url(prev_song)
            if source_url:
                state.current_source_url = source_url
                state.source_url_fetched_at = time.monotonic()
                await restart_playback_at_position(self.guild_id, 0.0, state)
                await update_now_playing_embed(self.guild_id)
                asyncio.create_task(_prefetch_next(self.guild_id))
        except Exception as e:
            logger.warning("Prev failed: %s", e)

    async def _rewind(self, interaction: Interaction):
        state = await self._check(interaction)
        if not state:
            return
        try:
            pos = max(0, state.get_playback_position() - 15)
            await restart_playback_at_position(self.guild_id, pos, state)
            state._last_embed_edit = time.monotonic()
            embed = build_now_playing_embed(state, self.guild_id)
            await interaction.response.edit_message(embed=embed)
        except Exception as e:
            logger.warning("Rewind failed: %s", e)
            if not interaction.response.is_done():
                await interaction.response.defer()

    async def _pause_resume(self, interaction: Interaction):
        state = await self._check(interaction)
        if not state:
            return
        try:
            if state.voice_client and state.voice_client.is_paused():
                if state.paused_at is not None:
                    pause_duration = time.monotonic() - state.paused_at
                    state.playback_start_time += pause_duration
                    state.paused_at = None
                state.voice_client.resume()
            elif state.voice_client and state.voice_client.is_playing():
                state.voice_client.pause()
                state.paused_at = time.monotonic()
            now = time.monotonic()
            if now - state._last_embed_edit < 1.0:
                await interaction.response.defer()
            else:
                state._last_embed_edit = now
                embed = build_now_playing_embed(state, self.guild_id)
                await interaction.response.edit_message(embed=embed)
        except Exception as e:
            logger.warning("Pause/resume failed: %s", e)
            if not interaction.response.is_done():
                await interaction.response.defer()

    async def _forward(self, interaction: Interaction):
        state = await self._check(interaction)
        if not state:
            return
        try:
            duration = (state.current_song or {}).get("duration") or 0
            pos = state.get_playback_position() + 15
            if duration and pos >= duration:
                await interaction.response.defer()
                if state.voice_client and state.voice_client.is_playing():
                    state.voice_client.stop()
                return
            await restart_playback_at_position(self.guild_id, pos, state)
            state._last_embed_edit = time.monotonic()
            embed = build_now_playing_embed(state, self.guild_id)
            await interaction.response.edit_message(embed=embed)
        except Exception as e:
            logger.warning("Forward failed: %s", e)
            if not interaction.response.is_done():
                await interaction.response.defer()

    async def _skip(self, interaction: Interaction):
        state = await self._check(interaction)
        if not state:
            return
        await interaction.response.defer()
        if state.queue:
            asyncio.create_task(_prefetch_next(self.guild_id))
        if state.voice_client and (state.voice_client.is_playing() or state.voice_client.is_paused()):
            state.voice_client.stop()

    async def _on_volume(self, interaction: Interaction):
        state = await self._check(interaction)
        if not state:
            return
        state.volume = int(interaction.data["values"][0]) / 100
        if state.voice_client and state.voice_client.source:
            state.voice_client.source.volume = state.volume
        now = time.monotonic()
        if now - state._last_embed_edit < 1.0:
            await interaction.response.defer()
        else:
            state._last_embed_edit = now
            embed = build_now_playing_embed(state, self.guild_id)
            await interaction.response.edit_message(embed=embed)

    async def _apply_filter_toggle(self, interaction: Interaction, filter_name: str):
        """Toggle a single filter and restart playback."""
        state = await self._check(interaction)
        if not state:
            return
        playing = state.voice_client and (state.voice_client.is_playing() or state.voice_client.is_paused())
        pos = state.get_playback_position() if playing else 0.0
        new_val = not state.audio_filters.get(filter_name, False)
        state.audio_filters[filter_name] = new_val
        if filter_name == "nightcore" and new_val:
            state.audio_filters["vaporwave"] = False
        elif filter_name == "vaporwave" and new_val:
            state.audio_filters["nightcore"] = False
        state.speed_multiplier = 1.0
        await interaction.response.defer()
        try:
            if playing:
                await restart_playback_at_position(self.guild_id, pos, state)
            await update_now_playing_embed(self.guild_id)
        except Exception as e:
            logger.error("Filter toggle failed: %s", e)

    async def _toggle_bass(self, interaction: Interaction):
        state = await self._check(interaction)
        if not state:
            return
        playing = state.voice_client and (state.voice_client.is_playing() or state.voice_client.is_paused())
        pos = state.get_playback_position() if playing else 0.0
        cur = state.audio_filters.get("bass_boost", 0)
        state.audio_filters["bass_boost"] = (cur + 1) % 4  # 0→1→2→3→0
        await interaction.response.defer()
        try:
            if playing:
                await restart_playback_at_position(self.guild_id, pos, state)
            await update_now_playing_embed(self.guild_id)
        except Exception as e:
            logger.error("Bass toggle failed: %s", e)

    async def _toggle_nightcore(self, interaction: Interaction):
        await self._apply_filter_toggle(interaction, "nightcore")

    async def _toggle_vaporwave(self, interaction: Interaction):
        await self._apply_filter_toggle(interaction, "vaporwave")

    async def _loop_toggle(self, interaction: Interaction):
        state = await self._check(interaction)
        if not state:
            return
        modes = ["off", "single", "queue", "shuffle"]
        idx = modes.index(state.loop_mode) if state.loop_mode in modes else 0
        state.loop_mode = modes[(idx + 1) % len(modes)]
        now = time.monotonic()
        if now - state._last_embed_edit < 1.0:
            await interaction.response.defer()
        else:
            state._last_embed_edit = now
            embed = build_now_playing_embed(state, self.guild_id)
            await interaction.response.edit_message(embed=embed)

    async def _stop(self, interaction: Interaction):
        state = await self._check(interaction)
        if not state:
            return
        state.clear_queue()
        state.current_song = None
        state.loop_mode = "off"
        if state._current_view is not None:
            state._current_view.stop()
            state._current_view = None
        if state.now_playing_updater and not state.now_playing_updater.done():
            state.now_playing_updater.cancel()
        if state.voice_client:
            state._play_generation += 1
            if state.voice_client.is_playing() or state.voice_client.is_paused():
                state.voice_client.stop()
            await safe_voice_disconnect(state.voice_client)
            state.voice_client = None
        await interaction.response.defer()
        try:
            await interaction.message.delete()
        except Exception:
            pass
        state.now_playing_message = None

    async def _clear_queue(self, interaction: Interaction):
        state = await self._check(interaction)
        if not state:
            return
        state.queue.clear()
        state.history.clear()
        await interaction.response.defer()
        await update_now_playing_embed(self.guild_id)

    async def _remove_song(self, interaction: Interaction):
        state = await self._check(interaction)
        if not state:
            return
        if not state.queue and not state.history:
            await interaction.response.send_message(t(self.guild_id, "nothing_to_remove"), ephemeral=True)
            return
        view = RemoveSongView(self.guild_id)
        await interaction.response.send_message(t(self.guild_id, "select_to_remove"), view=view, ephemeral=True)

    async def _on_queue_select(self, interaction: Interaction):
        state = await self._check(interaction)
        if not state:
            return
        val = interaction.data["values"][0]
        if val == "now_playing":
            await interaction.response.defer()
            return
        # Determine selected song
        if val.startswith("hist_"):
            h_idx = int(val[5:])
            if h_idx >= len(state.history):
                await interaction.response.send_message(t(self.guild_id, "song_unavailable"), ephemeral=True)
                return
            selected = state.history.pop(h_idx)
        else:
            idx = int(val)
            if idx >= len(state.queue):
                await interaction.response.send_message(t(self.guild_id, "song_not_in_queue"), ephemeral=True)
                return
            selected = state.queue.pop(idx)
        if state.current_song:
            state.history.append(state.current_song)
            if len(state.history) > HISTORY_MAX:
                state.history.pop(0)
        state.current_song = selected
        state._play_generation += 1
        await interaction.response.defer()
        source_url = await _get_stream_url(selected)
        if source_url:
            state.current_source_url = source_url
            state.source_url_fetched_at = time.monotonic()
            await restart_playback_at_position(self.guild_id, 0.0, state)
            await update_now_playing_embed(self.guild_id)
            asyncio.create_task(_prefetch_next(self.guild_id))


class RemoveSongView(View):
    """Ephemeral dropdown to remove a specific song from the queue or history."""

    def __init__(self, guild_id: int):
        super().__init__(timeout=30)
        self.guild_id = guild_id
        state = get_music_state(guild_id)
        options = []
        for i, song in enumerate(state.queue[:15]):
            dur = format_duration(song.get("duration")) if song.get("duration") else "?"
            label = song['title']
            if len(label) > 100:
                label = label[:97] + "..."
            options.append(discord.SelectOption(label=label, value=f"q_{i}",
                                                description=t(guild_id, "remove_upcoming_desc", dur=dur)))
        remaining = 25 - len(options)
        hist_shown = min(len(state.history), remaining)
        for j in range(hist_shown):
            h_idx = len(state.history) - 1 - j
            song = state.history[h_idx]
            dur = format_duration(song.get("duration")) if song.get("duration") else "?"
            label = song['title']
            if len(label) > 100:
                label = label[:97] + "..."
            options.append(discord.SelectOption(label=label, value=f"h_{h_idx}",
                                                description=t(guild_id, "remove_played_desc", dur=dur)))
        if not options:
            options.append(discord.SelectOption(label=t(guild_id, "remove_nothing_label"), value="none"))
        self.rm_select = Select(placeholder=t(guild_id, "remove_select_placeholder"), options=options,
                                min_values=1, max_values=1)
        self.rm_select.callback = self._on_remove
        self.add_item(self.rm_select)

    async def _on_remove(self, interaction: Interaction):
        state = get_music_state(self.guild_id)
        val = self.rm_select.values[0]
        if val == "none":
            await interaction.response.edit_message(content=t(self.guild_id, "nothing_to_remove"), view=None)
            return
        if val.startswith("q_"):
            idx = int(val[2:])
            if idx < len(state.queue):
                removed = state.queue.pop(idx)
                await interaction.response.edit_message(
                    content=t(self.guild_id, "removed_from_queue", title=removed['title']), view=None)
                _auto_delete(interaction.message, 3)
            else:
                await interaction.response.edit_message(
                    content=t(self.guild_id, "song_not_in_queue"), view=None)
        elif val.startswith("h_"):
            h_idx = int(val[2:])
            if h_idx < len(state.history):
                removed = state.history.pop(h_idx)
                await interaction.response.edit_message(
                    content=t(self.guild_id, "removed_from_history", title=removed['title']), view=None)
                _auto_delete(interaction.message, 3)
            else:
                await interaction.response.edit_message(
                    content=t(self.guild_id, "song_not_in_history"), view=None)
        await update_now_playing_embed(self.guild_id)


class FilterSelectView(View):
    """Interactive dropdown for audio filters and speed."""

    def __init__(self, guild_id: int):
        super().__init__(timeout=120)
        self.guild_id = guild_id
        state = get_music_state(guild_id)

        bass_level = state.audio_filters.get("bass_boost", 0)
        self.filter_select = Select(
            placeholder=t(guild_id, "filter_placeholder"),
            min_values=0,
            max_values=3,
            options=[
                discord.SelectOption(label=t(guild_id, "filter_bass_light"), value="bass_1",
                                     description=t(guild_id, "filter_bass_light_desc"),
                                     default=(bass_level == 1)),
                discord.SelectOption(label=t(guild_id, "filter_bass_medium"), value="bass_2",
                                     description=t(guild_id, "filter_bass_med_desc"),
                                     default=(bass_level == 2)),
                discord.SelectOption(label=t(guild_id, "filter_bass_heavy"), value="bass_3",
                                     description=t(guild_id, "filter_bass_heavy_desc"),
                                     default=(bass_level == 3)),
                discord.SelectOption(label=t(guild_id, "filter_nightcore"), value="nightcore",
                                     description=t(guild_id, "filter_nc_desc"),
                                     default=state.audio_filters.get("nightcore", False)),
                discord.SelectOption(label=t(guild_id, "filter_vaporwave"), value="vaporwave",
                                     description=t(guild_id, "filter_vw_desc"),
                                     default=state.audio_filters.get("vaporwave", False)),
            ],
        )
        self.filter_select.callback = self._on_filter
        self.add_item(self.filter_select)

    async def _on_filter(self, interaction: Interaction):
        state = get_music_state(self.guild_id)
        if not _interaction_in_voice(interaction, state):
            await interaction.response.send_message(t(self.guild_id, "need_bot_channel"), ephemeral=True)
            return
        selected = set(self.filter_select.values)
        if "nightcore" in selected and "vaporwave" in selected:
            await interaction.response.send_message(
                t(self.guild_id, "nightcore_vaporwave_exclusive"), ephemeral=True)
            return
        playing = state.voice_client and (state.voice_client.is_playing() or state.voice_client.is_paused())
        pos = state.get_playback_position() if playing else 0.0
        bass = 0
        for v in ("bass_1", "bass_2", "bass_3"):
            if v in selected:
                bass = int(v[-1])
        state.audio_filters["bass_boost"] = bass
        state.audio_filters["nightcore"] = "nightcore" in selected
        state.audio_filters["vaporwave"] = "vaporwave" in selected
        if playing:
            await interaction.response.defer()
            await restart_playback_at_position(self.guild_id, pos, state)
            await interaction.edit_original_response(
                embed=build_filters_embed(state, self.guild_id),
                view=FilterSelectView(self.guild_id))
        else:
            await interaction.response.edit_message(
                embed=build_filters_embed(state, self.guild_id),
                view=FilterSelectView(self.guild_id))
        await update_now_playing_embed(self.guild_id)



def build_filters_embed(state: "GuildMusicState", guild_id: int) -> Embed:
    """Build the filters status embed."""
    embed = create_embed(t(guild_id, "audio_filters"))
    for name, active in state.audio_filters.items():
        if name == "bass_boost":
            level_names = {0: "Off", 1: "Light", 2: "Medium", 3: "Heavy"}
            status = level_names.get(active, "Off")
        else:
            status = t(guild_id, "active") if active else t(guild_id, "inactive")
        embed.add_field(name=name.replace("_", " ").title(), value=status, inline=True)
    note = t(guild_id, "filters_restart_note") if state.current_song else t(guild_id, "filters_next_note")
    embed.add_field(name="ℹ️", value=note, inline=False)
    return embed


# ---------------------------------------------------------------------------
# Command guards: cooldown + voice channel checks
# ---------------------------------------------------------------------------

_cooldowns: Dict[int, float] = {}  # user_id -> last command timestamp
_cooldown_prune_counter: int = 0


def check_cooldown(user_id: int) -> bool:
    """Return True if the user is allowed to run a command (not rate-limited)."""
    global _cooldown_prune_counter
    now = time.monotonic()
    last = _cooldowns.get(user_id, 0.0)
    if now - last < COOLDOWN_SECONDS:
        return False
    _cooldowns[user_id] = now
    _cooldown_prune_counter += 1
    if _cooldown_prune_counter >= 100:
        _cooldown_prune_counter = 0
        cutoff = now - 60
        for uid in [k for k, v in _cooldowns.items() if v < cutoff]:
            del _cooldowns[uid]
    return True


def user_in_bot_channel(message: discord.Message, state: GuildMusicState) -> bool:
    """Check if the command author is in the same voice channel as the bot."""
    if not state.voice_client or not state.voice_client.is_connected():
        return True  # Bot not in a channel — no restriction
    if not message.author.voice:
        return False
    return message.author.voice.channel == state.voice_client.channel


# ---------------------------------------------------------------------------
# YouTube / yt-dlp helpers
# ---------------------------------------------------------------------------


def _extract_best_audio_url(data: dict) -> Optional[str]:
    """Extract the best audio stream URL from yt-dlp result data."""
    formats = data.get("formats")
    if formats:
        # Prefer audio-only formats sorted by bitrate
        audio_fmts = [
            f for f in formats
            if f.get("acodec") != "none" and f.get("vcodec") in ("none", None)
        ]
        if audio_fmts:
            audio_fmts.sort(key=lambda f: f.get("abr") or f.get("tbr") or 0, reverse=True)
            return audio_fmts[0].get("url")

        # Fallback: any format with a URL
        for f in reversed(formats):
            if f.get("url"):
                return f["url"]

    # Last resort: top-level url (only if it's a stream, not a page URL)
    url = data.get("url", "")
    if url and "youtube.com/watch" not in url and "youtu.be/" not in url:
        return url
    return None


async def fetch_ytdl_info(url: str, is_search: bool = False) -> Optional[dict]:
    """Fetch info via yt-dlp with automatic fallback for age-restricted content.

    Strategy:
      1. Try android_vr + web clients (fast, no JS challenges)
      2. If that fails, try subprocess with --js-runtimes and cookies
      3. If that also fails, auto-update yt-dlp and retry subprocess once
    """
    loop = asyncio.get_running_loop()

    if is_search and not url.startswith("http"):
        url = f"ytsearch{SEARCH_RESULTS_LIMIT}:{url}"

    # --- Attempt 1: library call (reuse instance) ---
    try:
        data = await loop.run_in_executor(
            None, lambda: _ytdl_instance.extract_info(url, download=False)
        )
        if data and (data.get("formats") or data.get("url") or data.get("entries")):
            return data
        logger.info("Primary extraction returned no usable data, trying fallback...")
    except Exception as exc:
        logger.info("Primary extraction failed (%s), trying fallback...", type(exc).__name__)

    # --- Attempt 2: subprocess with JS solver + cookies ---
    try:
        return await _fetch_ytdl_subprocess(url)
    except Exception as exc:
        logger.warning("Subprocess fallback also failed: %s", exc)

    # --- Attempt 3: auto-update yt-dlp and retry ---
    if _should_try_update():
        try:
            updated, old_ver, new_ver = await _update_ytdlp()
            if updated:
                logger.info("yt-dlp updated %s -> %s after failure, retrying...", old_ver, new_ver)
                return await _fetch_ytdl_subprocess(url)
        except Exception as exc:
            logger.error("Auto-update retry failed: %s", exc)

    return None


async def _fetch_ytdl_subprocess(url: str) -> Optional[dict]:
    """Fallback: run yt-dlp as a subprocess with JS runtime for age-restricted content."""
    loop = asyncio.get_running_loop()

    def _run():
        cmd = [
            "yt-dlp",
            "--format", "bestaudio/best",
            "--js-runtimes", "node",
            "--remote-components", "ejs:github",
            "-j",
            "--no-download",
            "--no-warnings",
            "--geo-bypass",
            "--default-search", "ytsearch",
        ]
        if COOKIE_FILE.exists():
            cmd.extend(["--cookies", str(COOKIE_FILE)])
        cmd.extend(["--", url])

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=90
        )
        if result.returncode != 0:
            stderr = result.stderr[:500] if result.stderr else "unknown error"
            raise RuntimeError(f"yt-dlp subprocess failed: {stderr}")
        return json.loads(result.stdout)

    try:
        return await loop.run_in_executor(None, _run)
    except Exception as exc:
        logger.error("Subprocess fallback error: %s", exc)
        raise


async def _get_stream_url(song: dict) -> Optional[str]:
    """Get a stream URL for a song, using cache when fresh."""
    url = song.get("webpage_url") or song["url"]
    cached = _stream_cache.get(url)
    if cached:
        stream_url, ts = cached
        if time.monotonic() - ts < STREAM_URL_TTL:
            return stream_url

    inflight = _stream_inflight.get(url)
    if inflight is not None:
        return await inflight

    loop = asyncio.get_running_loop()
    fut: asyncio.Future[Optional[str]] = loop.create_future()
    _stream_inflight[url] = fut
    try:
        data = await fetch_ytdl_info(url)
        if not data:
            fut.set_result(None)
            return None
        if "entries" in data:
            data = data["entries"][0]
        stream_url = _extract_best_audio_url(data)
        if stream_url:
            if url in _stream_cache:
                try:
                    _stream_cache_order.remove(url)
                except ValueError:
                    pass
            _stream_cache[url] = (stream_url, time.monotonic())
            _stream_cache_order.append(url)
            while len(_stream_cache) > 50:
                old_key = _stream_cache_order.popleft()
                _stream_cache.pop(old_key, None)
        fut.set_result(stream_url)
        return stream_url
    except Exception as exc:
        fut.set_exception(exc)
        raise
    finally:
        _stream_inflight.pop(url, None)


async def _prefetch_next(guild_id: int):
    """Pre-fetch the next song's stream URL in the background."""
    state = get_music_state(guild_id)
    if not state.queue:
        return
    next_song = state.queue[0]
    url = next_song.get("webpage_url") or next_song["url"]
    cached = _stream_cache.get(url)
    if cached and time.monotonic() - cached[1] < STREAM_URL_TTL:
        return
    try:
        await _get_stream_url(next_song)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Voice helpers
# ---------------------------------------------------------------------------


async def resilient_voice_connect(channel, max_retries: int = 5):
    """Connect to a voice channel with exponential back-off retries."""
    for attempt in range(max_retries):
        try:
            return await channel.connect(timeout=30.0)
        except ConnectionClosed as exc:
            if exc.code == 4017 and attempt < max_retries - 1:
                delay = 5 * (2 ** attempt)
                logger.warning(
                    "Voice connect attempt %d/%d failed (4017), retrying in %ds...",
                    attempt + 1, max_retries, delay,
                )
                await asyncio.sleep(delay)
                continue
            raise
        except asyncio.TimeoutError:
            if attempt < max_retries - 1:
                logger.warning("Voice connect attempt %d/%d timed out", attempt + 1, max_retries)
                await asyncio.sleep(5)
                continue
            raise
        except Exception:
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
                continue
            raise


async def safe_voice_disconnect(vc):
    """Disconnect from voice without raising."""
    if not vc:
        return
    try:
        if vc.is_connected():
            await vc.disconnect()
    except (ConnectionClosed, discord.errors.NotFound, AttributeError):
        pass
    except Exception as exc:
        logger.warning("Voice disconnect error: %s", exc)


async def check_inactivity(guild_id: int):
    """Auto-disconnect after INACTIVITY_TIMEOUT seconds of silence."""
    await asyncio.sleep(INACTIVITY_TIMEOUT)
    state = get_music_state(guild_id)
    if (
        state.voice_client
        and state.voice_client.is_connected()
        and not state.voice_client.is_playing()
        and not state.voice_client.is_paused()
        and len(state.queue) == 0
        and len(state.voice_client.channel.members) <= 1
    ):
        if state._current_view is not None:
            state._current_view.stop()
        if state.now_playing_updater and not state.now_playing_updater.done():
            state.now_playing_updater.cancel()
        try:
            await state.voice_client.disconnect()
        except (ConnectionClosed, discord.errors.NotFound):
            pass
        music_states.pop(guild_id, None)
        logger.info("Inactivity disconnect: guild %d", guild_id)


async def _auto_leave_empty_channel(guild_id: int, state: GuildMusicState):
    """Wait 60s then leave if still alone. Cancels cleanly if someone rejoins."""
    await asyncio.sleep(60)
    if (
        state.voice_client
        and state.voice_client.is_connected()
        and len([m for m in state.voice_client.channel.members if not m.bot]) == 0
    ):
        if state._current_view is not None:
            state._current_view.stop()
        if state.now_playing_updater and not state.now_playing_updater.done():
            state.now_playing_updater.cancel()
        await safe_voice_disconnect(state.voice_client)
        music_states.pop(guild_id, None)
        logger.info("Auto-disconnect (empty channel): guild %d", guild_id)


# ---------------------------------------------------------------------------
# Playback engine
# ---------------------------------------------------------------------------


async def play_next_in_queue(guild_id: int):
    state = get_music_state(guild_id)
    reconnect_channel = None  # set if we need to reconnect after releasing the lock
    skip_to_next = False      # set if we need to advance after releasing the lock

    async with state.play_lock:
        # Determine next song based on loop mode
        if state.loop_mode == "single" and state.current_song:
            next_song = state.current_song
        elif state.queue:
            if state.loop_mode == "shuffle":
                idx = random.randrange(len(state.queue))
                next_song = state.queue.pop(idx)
            else:
                next_song = state.queue.pop(0)
            if state.loop_mode in ("queue", "shuffle") and state.current_song:
                state.queue.append(state.current_song)
            # Save outgoing song to history
            if state.current_song and state.current_song != next_song:
                state.history.append(state.current_song)
                if len(state.history) > HISTORY_MAX:
                    state.history.pop(0)
            state.current_song = next_song
        else:
            state.current_song = None
            if state.inactivity_task:
                state.inactivity_task.cancel()
            state.inactivity_task = asyncio.create_task(check_inactivity(guild_id))
            return

        if not state.voice_client or not state.voice_client.is_connected():
            await safe_voice_disconnect(state.voice_client)
            state.voice_client = None
            logger.warning("Guild %d: voice client gone, stopping playback", guild_id)
            return

        try:
            source_url = await _get_stream_url(next_song)
            if not source_url:
                raise ValueError(f"No playable stream for {next_song['title']}")

            # Delete previous "now playing" embed and cancel updater
            if state.now_playing_updater and not state.now_playing_updater.done():
                state.now_playing_updater.cancel()
            if state.now_playing_message:
                try:
                    await state.now_playing_message.delete()
                except Exception:
                    pass

            # Reset position tracking
            state.current_source_url = source_url
            state.source_url_fetched_at = time.monotonic()
            state.playback_offset = 0.0
            state.paused_at = None

            channel = client.get_channel(next_song["channel_id"])

            # Build audio source and start playback BEFORE sending embed
            # so the View is constructed while is_playing() is True
            current_ffmpeg = state.get_ffmpeg_options()
            raw_source = discord.FFmpegPCMAudio(
                source_url,
                before_options=current_ffmpeg.get("before_options", ""),
                options=current_ffmpeg.get("options", ""),
            )
            audio_source = discord.PCMVolumeTransformer(raw_source, volume=state.volume)

            state._play_generation += 1
            gen = state._play_generation

            def after_playback(error):
                if state._play_generation != gen:
                    return  # stale callback
                if error:
                    logger.error("Playback error: %s", error)
                asyncio.run_coroutine_threadsafe(play_next_in_queue(guild_id), client.loop)

            try:
                state.voice_client.play(audio_source, after=after_playback)
                state.playback_start_time = time.monotonic()
                state.last_activity = datetime.now(UTC)

                embed = build_now_playing_embed(state, guild_id)
                view = NowPlayingView(guild_id)
                if state._current_view is not None:
                    state._current_view.stop()
                state._current_view = view
                state.now_playing_message = await channel.send(embed=embed, view=view)

                if state.now_playing_updater and not state.now_playing_updater.done():
                    state.now_playing_updater.cancel()
                state.now_playing_updater = asyncio.create_task(now_playing_update_loop(guild_id))
                asyncio.create_task(_prefetch_next(guild_id))
            except ConnectionClosed as exc:
                if exc.code == 4017:
                    logger.warning("Voice disconnected during play (4017), will reconnect...")
                    reconnect_channel = state.voice_client.channel if state.voice_client else None
                    await safe_voice_disconnect(state.voice_client)
                    state.voice_client = None
                    if state.current_song:
                        state.queue.insert(0, state.current_song)
                        state.current_song = None
                    # Don't recurse inside the lock — handled below
                else:
                    raise

        except Exception as exc:
            logger.error("Error playing song: %s", exc)
            channel = client.get_channel(next_song["channel_id"])
            if channel:
                await channel.send(
                    embed=create_embed(
                        t(guild_id, "playback_error"),
                        t(guild_id, "playback_error_desc", title=next_song["title"]),
                        Color.red(),
                    ),
                    delete_after=10,
                )
            if state.queue:
                skip_to_next = True
            # Don't recurse inside the lock — handled below

    # --- Outside the lock: safe to recurse ---
    if reconnect_channel:
        try:
            await asyncio.sleep(5)
            state.voice_client = await resilient_voice_connect(reconnect_channel)
            await play_next_in_queue(guild_id)
        except Exception as exc:
            logger.error("Reconnect after 4017 failed: %s", exc)
    elif skip_to_next:
        await play_next_in_queue(guild_id)


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


@client.event
async def on_ready():
    logger.info("%s is online and ready!", client.user)
    print(f"Bot {client.user} is online!")
    await client.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="music | //help")
    )
    # Start background auto-update loop
    asyncio.create_task(_auto_update_loop())


@client.event
async def on_guild_join(guild: discord.Guild):
    if len(client.guilds) > MAX_GUILDS:
        logger.warning("Guild limit reached (%d/%d), leaving %s (%d)",
                        len(client.guilds), MAX_GUILDS, guild.name, guild.id)
        await guild.leave()


@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    # Bot was kicked/disconnected
    if member == client.user and before.channel and not after.channel:
        state = music_states.pop(before.channel.guild.id, None)
        if state:
            if state._current_view is not None:
                state._current_view.stop()
            if state.now_playing_updater and not state.now_playing_updater.done():
                state.now_playing_updater.cancel()
        logger.info("Disconnected from guild %d", before.channel.guild.id)

    # Someone left — check if bot is now alone
    if member != client.user and before.channel and before.channel != after.channel:
        for guild_id, state in list(music_states.items()):
            if (
                state.voice_client
                and state.voice_client.is_connected()
                and state.voice_client.channel == before.channel
            ):
                humans = [m for m in state.voice_client.channel.members if not m.bot]
                if len(humans) == 0:
                    # Cancel any existing auto-leave task to avoid duplicates
                    if state.auto_leave_task and not state.auto_leave_task.done():
                        state.auto_leave_task.cancel()
                    state.auto_leave_task = asyncio.create_task(
                        _auto_leave_empty_channel(guild_id, state)
                    )
                else:
                    # Someone joined back — cancel pending auto-leave
                    if state.auto_leave_task and not state.auto_leave_task.done():
                        state.auto_leave_task.cancel()
                        state.auto_leave_task = None


# ---------------------------------------------------------------------------
# Command routing
# ---------------------------------------------------------------------------

# Commands listed longest-first so "//nowplaying" matches before "//np", etc.
# Each entry: (prefix, handler_name, needs_exact_or_space)
# We use a helper to avoid startswith collisions like /play matching /playlist.


def _match_command(content: str, prefix: str) -> bool:
    """Return True if content is exactly the prefix, or prefix followed by a space."""
    return content == prefix or content.startswith(prefix + " ")


# ---------------------------------------------------------------------------
# Help topic mapping (key -> (title_key, body_key) in lang.py)
# ---------------------------------------------------------------------------

_HELP_TOPIC_KEYS = {
    "play": ("help_play_title", "help_play_body"),
    "playtop": ("help_playtop_title", "help_playtop_body"),
    "search": ("help_search_title", "help_search_body"),
    "pause": ("help_pause_title", "help_pause_body"),
    "resume": ("help_pause_title", "help_pause_body"),
    "skip": ("help_skip_title", "help_skip_body"),
    "skipto": ("help_skipto_title", "help_skipto_body"),
    "replay": ("help_replay_title", "help_replay_body"),
    "stop": ("help_stop_title", "help_stop_body"),
    "queue": ("help_queue_title", "help_queue_body"),
    "q": ("help_queue_title", "help_queue_body"),
    "np": ("help_np_title", "help_np_body"),
    "nowplaying": ("help_np_title", "help_np_body"),
    "shuffle": ("help_shuffle_title", "help_shuffle_body"),
    "clear": ("help_clear_title", "help_clear_body"),
    "remove": ("help_remove_title", "help_remove_body"),
    "swap": ("help_swap_title", "help_swap_body"),
    "volume": ("help_volume_title", "help_volume_body"),
    "vol": ("help_volume_title", "help_volume_body"),
    "loop": ("help_loop_title", "help_loop_body"),
    "move": ("help_move_title", "help_move_body"),
    "filters": ("help_filters_title", "help_filters_body"),
    "bass": ("help_filters_title", "help_filters_body"),
    "nightcore": ("help_filters_title", "help_filters_body"),
    "vaporwave": ("help_filters_title", "help_filters_body"),
    "ping": ("help_ping_title", "help_ping_body"),
    "lang": ("help_lang_title", "help_lang_body"),
    "ask": ("help_ask_title", "help_ask_body"),
    "personality": ("help_personality_title", "help_personality_body"),
}

_HELP_VISIBLE_TOPICS = sorted({
    k for k in _HELP_TOPIC_KEYS
    if k not in ("q", "vol", "np", "nowplaying", "resume")
})


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Ignore DMs — all commands require a guild context
    if not message.guild:
        return

    content = message.content
    if not content.startswith("//"):
        return

    gid = message.guild.id  # shorthand used by all command handlers

    # Ban/timeout check (owner is always exempt)
    if message.author.id != OWNER_ID and is_banned_or_timed_out(message.author.id):
        return

    # Cooldown check (exempt read-only commands)
    _exempt = ("//help", "//np", "//nowplaying", "//queue", "//q", "//ping", "//filters", "//lang", "//personality")
    if not any(content.startswith(p) for p in _exempt):
        if not check_cooldown(message.author.id):
            return  # silently drop spammed commands

    # --- /start ---
    if _match_command(content, "//start"):
        state = get_music_state(gid)
        try:
            if not state.voice_client or not state.voice_client.is_connected():
                if message.author.voice:
                    state.voice_client = await resilient_voice_connect(message.author.voice.channel)
                else:
                    await message.channel.send(t(gid, "need_voice"))
                    return
            embed = Embed(
                title=t(gid, "player_title"),
                description=t(gid, "player_idle_desc"),
                color=Color.from_rgb(30, 215, 96),
            )
            view = IdlePlayerView(gid)
            if state._current_view is not None:
                state._current_view.stop()
            state._current_view = view
            state.now_playing_message = await message.channel.send(embed=embed, view=view)
            if state.now_playing_updater and not state.now_playing_updater.done():
                state.now_playing_updater.cancel()
        except Exception as exc:
            logger.error("Error in /start: %s", exc)
            await message.channel.send(
                embed=create_embed(t(gid, "error"), sanitize_error(exc), Color.red()))
        try:
            await message.delete()
        except Exception:
            pass
        return

    # --- /play ---
    if _match_command(content, "//play"):
        args = content.split(maxsplit=1)
        if len(args) < 2:
            await message.channel.send(t(gid, "provide_song"))
            return

        query = args[1]
        state = get_music_state(gid)

        try:
            # Connect to voice if needed
            if not state.voice_client or not state.voice_client.is_connected():
                if message.author.voice:
                    try:
                        state.voice_client = await resilient_voice_connect(message.author.voice.channel)
                    except Exception as exc:
                        await message.channel.send(
                            embed=create_embed(t(gid, "connection_failed"), sanitize_error(exc), Color.red())
                        )
                        return
                else:
                    await message.channel.send(t(gid, "need_voice"))
                    return

            # Must be in the same channel as the bot
            if not user_in_bot_channel(message, state):
                await message.channel.send(t(gid, "need_same_channel"))
                return

            loading_msg = await message.channel.send(t(gid, "searching"))
            data = await fetch_ytdl_info(query)

            if data is None:
                await loading_msg.edit(content=t(gid, "song_not_found"))
                return

            # Playlist
            if "entries" in data:
                entries = [e for e in data["entries"] if e]
                available_slots = MAX_QUEUE_LENGTH - len(state.queue)
                if available_slots <= 0:
                    await loading_msg.edit(content=t(gid, "queue_full", max=MAX_QUEUE_LENGTH))
                    return

                if len(entries) > available_slots:
                    entries = entries[:available_slots]

                for entry in entries:
                    state.add_to_queue({
                        "url": entry.get("webpage_url") or entry.get("url"),
                        "title": entry.get("title", "Unknown"),
                        "channel_id": message.channel.id,
                        "thumbnail": _best_thumbnail(entry),
                        "duration": entry.get("duration"),
                        "uploader": entry.get("uploader"),
                        "webpage_url": entry.get("webpage_url"),
                        "view_count": entry.get("view_count"),
                    })

                await loading_msg.edit(
                    content=None,
                    embed=create_embed(
                        t(gid, "playlist_added"),
                        t(gid, "playlist_added_desc", count=len(entries)),
                        Color.green(),
                    ),
                )
                _auto_delete(loading_msg, 5)

            # Single song
            else:
                song_data = {
                    "url": data.get("webpage_url") or data.get("url"),
                    "title": data.get("title", "Unknown"),
                    "channel_id": message.channel.id,
                    "thumbnail": _best_thumbnail(data),
                    "duration": data.get("duration"),
                    "uploader": data.get("uploader"),
                    "webpage_url": data.get("webpage_url"),
                    "view_count": data.get("view_count"),
                }

                if not state.add_to_queue(song_data):
                    await loading_msg.edit(content=t(gid, "queue_full", max=MAX_QUEUE_LENGTH))
                    return

                embed = create_song_embed(song_data, t(gid, "added_to_queue"), gid)
                embed.add_field(name=t(gid, "position"), value=f"#{len(state.queue)}", inline=True)
                await loading_msg.edit(content=None, embed=embed)
                _auto_delete(loading_msg, 5)

            # Delete the user's command message to keep chat clean
            try:
                await message.delete()
            except Exception:
                pass

            if not state.voice_client.is_playing() and not state.voice_client.is_paused():
                await play_next_in_queue(gid)
            else:
                asyncio.create_task(_prefetch_next(gid))

        except Exception as exc:
            logger.error("Error in /play: %s", exc)
            await message.channel.send(
                embed=create_embed(t(gid, "error"), sanitize_error(exc), Color.red())
            )

    # --- /pause ---
    elif _match_command(content, "//pause"):
        state = get_music_state(gid)
        if not user_in_bot_channel(message, state):
            await message.channel.send(t(gid, "need_bot_channel"))
            return
        if state.voice_client and state.voice_client.is_playing():
            state.voice_client.pause()
            state.paused_at = time.monotonic()
            msg = await message.channel.send(t(gid, "paused"))
            _auto_delete(msg, 3)
        else:
            msg = await message.channel.send(t(gid, "nothing_playing"))
            _auto_delete(msg, 3)
        try:
            await message.delete()
        except Exception:
            pass

    # --- /resume ---
    elif _match_command(content, "//resume"):
        state = get_music_state(gid)
        if not user_in_bot_channel(message, state):
            await message.channel.send(t(gid, "need_bot_channel"))
            return
        if state.voice_client and state.voice_client.is_paused():
            if state.paused_at is not None:
                pause_duration = time.monotonic() - state.paused_at
                state.playback_start_time += pause_duration
                state.paused_at = None
            state.voice_client.resume()
            msg = await message.channel.send(t(gid, "resumed"))
            _auto_delete(msg, 3)
        else:
            msg = await message.channel.send(t(gid, "nothing_paused"))
            _auto_delete(msg, 3)
        try:
            await message.delete()
        except Exception:
            pass

    # --- /stop ---
    elif _match_command(content, "//stop"):
        state = get_music_state(gid)
        if not user_in_bot_channel(message, state):
            await message.channel.send(t(gid, "need_bot_channel"))
            return
        if state.voice_client:
            state.clear_queue()
            state.current_song = None
            state.loop_mode = "off"
            if state._current_view is not None:
                state._current_view.stop()
                state._current_view = None
            if state.now_playing_updater and not state.now_playing_updater.done():
                state.now_playing_updater.cancel()
            state._play_generation += 1  # invalidate old callbacks
            if state.voice_client.is_playing() or state.voice_client.is_paused():
                state.voice_client.stop()
            await safe_voice_disconnect(state.voice_client)
            state.voice_client = None
            if state.now_playing_message:
                try:
                    await state.now_playing_message.delete()
                except Exception:
                    pass
            music_states.pop(gid, None)
            msg = await message.channel.send(t(gid, "stopped"))
            _auto_delete(msg, 3)
        else:
            msg = await message.channel.send(t(gid, "not_connected"))
            _auto_delete(msg, 3)
        try:
            await message.delete()
        except Exception:
            pass

    # --- /skip ---
    elif _match_command(content, "//skip"):
        state = get_music_state(gid)
        if not user_in_bot_channel(message, state):
            await message.channel.send(t(gid, "need_bot_channel"))
            return
        if state.voice_client and (state.voice_client.is_playing() or state.voice_client.is_paused()):
            was_looping_single = state.loop_mode == "single"
            if was_looping_single:
                state.loop_mode = "off"
            state.voice_client.stop()
            if was_looping_single and state.queue:
                state.loop_mode = "single"
            msg = await message.channel.send(t(gid, "skipped"))
            _auto_delete(msg, 3)
        else:
            msg = await message.channel.send(t(gid, "nothing_playing"))
            _auto_delete(msg, 3)
        try:
            await message.delete()
        except Exception:
            pass

    # --- /skipto ---
    elif _match_command(content, "//skipto"):
        state = get_music_state(gid)
        if not user_in_bot_channel(message, state):
            await message.channel.send(t(gid, "need_bot_channel"))
            return
        args = content.split()
        if len(args) < 2:
            await message.channel.send(t(gid, "skipto_usage"))
            return
        try:
            pos = int(args[1]) - 1  # 1-indexed for users
            if pos < 0 or pos >= len(state.queue):
                await message.channel.send(t(gid, "skipto_invalid", count=len(state.queue)))
                return
            # Discard songs before the target
            skipped = pos
            state.queue = state.queue[pos:]
            # Stop current song — after_playback will trigger play_next_in_queue
            if state.voice_client and (state.voice_client.is_playing() or state.voice_client.is_paused()):
                state.voice_client.stop()
            await message.channel.send(t(gid, "skipto_msg", count=skipped, title=state.queue[0]["title"]))
        except ValueError:
            await message.channel.send(t(gid, "invalid_number"))

    # --- /search ---
    elif _match_command(content, "//search"):
        args = content.split(maxsplit=1)
        if len(args) < 2:
            await message.channel.send(t(gid, "search_usage"))
            return

        try:
            loading_msg = await message.channel.send(t(gid, "searching"))
            data = await fetch_ytdl_info(args[1], is_search=True)

            if data and "entries" in data and data["entries"]:
                results = [r for r in data["entries"] if r][:SEARCH_RESULTS_LIMIT]
                embed = create_embed(t(gid, "search_results", query=args[1]))
                for i, result in enumerate(results, 1):
                    duration = format_duration(result.get("duration"))
                    uploader = result.get("uploader", "Unknown")
                    url = result.get("webpage_url") or result.get("url", "")
                    embed.add_field(
                        name=f"{i}. {result.get('title', 'Unknown')}",
                        value=f"**{t(gid, 'channel_field')}:** {uploader} | **{t(gid, 'duration_field')}:** {duration}\n`/play {url}`",
                        inline=False,
                    )
                await loading_msg.edit(content=None, embed=embed)
            else:
                await loading_msg.edit(content=t(gid, "no_results"))
        except Exception as exc:
            logger.error("Search error: %s", exc)
            await message.channel.send(embed=create_embed(t(gid, "search_error"), sanitize_error(exc), Color.red()))

    # --- /queue | /q ---
    elif _match_command(content, "//queue") or _match_command(content, "//q"):
        state = get_music_state(gid)
        if not state.current_song and not state.queue:
            await message.channel.send(t(gid, "queue_empty"))
            return

        embed = create_embed(t(gid, "music_queue"))
        if state.current_song:
            current = f"🎵 **[{state.current_song['title']}]({state.current_song.get('webpage_url', state.current_song.get('url', ''))})**"
            if state.current_song.get("duration"):
                current += f" — `{format_duration(state.current_song['duration'])}`"
            if state.loop_mode != "off":
                current += f" {'🔂' if state.loop_mode == 'single' else '🔁'}"
            embed.add_field(name=t(gid, "now_playing"), value=current, inline=False)

        if state.queue:
            lines = []
            for s in state.queue[:10]:
                dur = f" `{format_duration(s['duration'])}`" if s.get("duration") else ""
                lines.append(f"{s['title']}{dur}")
            if len(state.queue) > 10:
                lines.append(t(gid, "and_more", count=len(state.queue) - 10))
            embed.add_field(
                name=t(gid, "up_next_count", count=len(state.queue)),
                value="\n".join(lines),
                inline=False,
            )

        embed.add_field(name=t(gid, "volume_field"), value=f"🔊 {int(state.volume * 100)}%", inline=True)
        if state.loop_mode != "off":
            embed.add_field(
                name=t(gid, "loop_field"),
                value=f"{'🔂' if state.loop_mode == 'single' else '🔁'} {state.loop_mode.capitalize()}",
                inline=True,
            )

        await message.channel.send(embed=embed)

    # --- /nowplaying | /np ---
    elif _match_command(content, "//nowplaying") or _match_command(content, "//np"):
        state = get_music_state(gid)
        if state.current_song:
            if state.now_playing_message:
                try:
                    await state.now_playing_message.delete()
                except Exception:
                    pass
            embed = build_now_playing_embed(state, gid)
            view = NowPlayingView(gid)
            if state._current_view is not None:
                state._current_view.stop()
            state._current_view = view
            state.now_playing_message = await message.channel.send(embed=embed, view=view)
        else:
            await message.channel.send(t(gid, "nothing_playing"))

    # --- /volume | /vol ---
    elif _match_command(content, "//volume") or _match_command(content, "//vol"):
        state = get_music_state(gid)
        if not user_in_bot_channel(message, state):
            await message.channel.send(t(gid, "need_bot_channel"))
            return
        args = content.split()
        if len(args) == 1:
            await message.channel.send(t(gid, "volume_current", vol=int(state.volume * 100)))
            return
        try:
            vol = int(args[1])
            if not (0 <= vol <= 200):
                await message.channel.send(t(gid, "volume_range"))
                return
            state.volume = vol / 100
            if state.voice_client and state.voice_client.source:
                state.voice_client.source.volume = state.volume
            await message.channel.send(t(gid, "volume_set", vol=vol))
        except ValueError:
            await message.channel.send(t(gid, "invalid_volume"))

    # --- /loop ---
    elif _match_command(content, "//loop"):
        state = get_music_state(gid)
        if not user_in_bot_channel(message, state):
            await message.channel.send(t(gid, "need_bot_channel"))
            return
        args = content.split()
        if len(args) == 1:
            modes = ["off", "single", "queue"]
            state.loop_mode = modes[(modes.index(state.loop_mode) + 1) % 3]
        else:
            mode = args[1].lower()
            valid = {"off", "none", "no", "single", "one", "song", "queue", "all"}
            if mode not in valid:
                await message.channel.send(t(gid, "invalid_loop"))
                return
            if mode in ("off", "none", "no"):
                state.loop_mode = "off"
            elif mode in ("single", "one", "song"):
                state.loop_mode = "single"
            else:
                state.loop_mode = "queue"

        loop_keys = {"off": "loop_off", "single": "loop_single", "queue": "loop_queue"}
        await message.channel.send(t(gid, loop_keys[state.loop_mode]))

    # --- /shuffle ---
    elif _match_command(content, "//shuffle"):
        state = get_music_state(gid)
        if not user_in_bot_channel(message, state):
            await message.channel.send(t(gid, "need_bot_channel"))
            return
        if len(state.queue) < 2:
            await message.channel.send(t(gid, "need_2_songs"))
            return
        state.shuffle_queue()
        await message.channel.send(t(gid, "shuffled", count=len(state.queue)))

    # --- /clear ---
    elif _match_command(content, "//clear"):
        state = get_music_state(gid)
        if not user_in_bot_channel(message, state):
            await message.channel.send(t(gid, "need_bot_channel"))
            return
        if not state.queue and not state.history:
            await message.channel.send(t(gid, "queue_already_empty"))
            return
        count = len(state.queue)
        state.queue.clear()
        state.history.clear()
        await message.channel.send(t(gid, "cleared", count=count))

    # --- /remove ---
    elif _match_command(content, "//remove"):
        state = get_music_state(gid)
        if not user_in_bot_channel(message, state):
            await message.channel.send(t(gid, "need_bot_channel"))
            return
        args = content.split()
        if len(args) < 2:
            await message.channel.send(t(gid, "remove_usage"))
            return
        try:
            removed = state.remove_from_queue(int(args[1]) - 1)
            if removed:
                await message.channel.send(t(gid, "removed", title=removed["title"]))
            else:
                await message.channel.send(t(gid, "invalid_position"))
        except ValueError:
            await message.channel.send(t(gid, "invalid_number"))

    # --- /move ---
    elif _match_command(content, "//move"):
        state = get_music_state(gid)
        if not state.voice_client or not state.voice_client.is_connected():
            await message.channel.send(t(gid, "bot_not_in_voice"))
            return
        if not message.author.voice:
            await message.channel.send(t(gid, "need_voice"))
            return
        target_channel = message.author.voice.channel
        if target_channel == state.voice_client.channel:
            await message.channel.send(t(gid, "already_in_channel"))
            return
        await state.voice_client.move_to(target_channel)
        await message.channel.send(t(gid, "moved", channel=target_channel.name))

    # --- /replay ---
    elif _match_command(content, "//replay"):
        state = get_music_state(gid)
        if not user_in_bot_channel(message, state):
            await message.channel.send(t(gid, "need_bot_channel"))
            return
        if not state.current_song:
            await message.channel.send(t(gid, "nothing_to_replay"))
            return
        # Re-insert current song at front and stop (triggers after_playback -> play_next)
        state.queue.insert(0, state.current_song)
        state.current_song = None
        old_loop = state.loop_mode
        state.loop_mode = "off"  # Prevent single-loop from blocking the restart
        if state.voice_client and (state.voice_client.is_playing() or state.voice_client.is_paused()):
            state.voice_client.stop()
        state.loop_mode = old_loop
        await message.channel.send(t(gid, "replay_msg"))

    # --- /playtop ---
    elif _match_command(content, "//playtop"):
        args = content.split(maxsplit=1)
        if len(args) < 2:
            await message.channel.send(t(gid, "playtop_usage"))
            return

        query = args[1]
        state = get_music_state(gid)

        if not state.voice_client or not state.voice_client.is_connected():
            # Treat like /play if not connected
            if message.author.voice:
                try:
                    state.voice_client = await resilient_voice_connect(message.author.voice.channel)
                except Exception as exc:
                    await message.channel.send(embed=create_embed(t(gid, "connection_failed"), sanitize_error(exc), Color.red()))
                    return
            else:
                await message.channel.send(t(gid, "need_voice"))
                return

        if not user_in_bot_channel(message, state):
            await message.channel.send(t(gid, "need_same_channel"))
            return

        try:
            loading_msg = await message.channel.send(t(gid, "searching"))
            data = await fetch_ytdl_info(query)

            if data is None:
                await loading_msg.edit(content=t(gid, "song_not_found"))
                return

            if "entries" in data:
                await loading_msg.edit(content=t(gid, "playtop_no_playlist"))
                return

            song_data = {
                "url": data.get("webpage_url") or data.get("url"),
                "title": data.get("title", "Unknown"),
                "channel_id": message.channel.id,
                "thumbnail": _best_thumbnail(data),
                "duration": data.get("duration"),
                "uploader": data.get("uploader"),
                "webpage_url": data.get("webpage_url"),
                "view_count": data.get("view_count"),
            }

            if len(state.queue) >= MAX_QUEUE_LENGTH:
                await loading_msg.edit(content=t(gid, "queue_full", max=MAX_QUEUE_LENGTH))
                return

            state.queue.insert(0, song_data)
            state.last_activity = datetime.now(UTC)

            embed = create_song_embed(song_data, t(gid, "added_to_top"), gid)
            embed.add_field(name=t(gid, "position"), value=t(gid, "next_up"), inline=True)
            await loading_msg.edit(content=None, embed=embed)
            _auto_delete(loading_msg, 5)

            try:
                await message.delete()
            except Exception:
                pass

            if not state.voice_client.is_playing() and not state.voice_client.is_paused():
                await play_next_in_queue(gid)
            else:
                asyncio.create_task(_prefetch_next(gid))

        except Exception as exc:
            logger.error("Error in /playtop: %s", exc)
            await message.channel.send(embed=create_embed(t(gid, "error"), sanitize_error(exc), Color.red()))

    # --- /swap ---
    elif _match_command(content, "//swap"):
        state = get_music_state(gid)
        if not user_in_bot_channel(message, state):
            await message.channel.send(t(gid, "need_bot_channel"))
            return
        args = content.split()
        if len(args) < 3:
            await message.channel.send(t(gid, "swap_usage"))
            return
        try:
            a, b = int(args[1]) - 1, int(args[2]) - 1
            if a < 0 or b < 0 or a >= len(state.queue) or b >= len(state.queue):
                await message.channel.send(t(gid, "swap_range", count=len(state.queue)))
                return
            if a == b:
                await message.channel.send(t(gid, "swap_same"))
                return
            state.queue[a], state.queue[b] = state.queue[b], state.queue[a]
            await message.channel.send(
                t(gid, "swapped", a=state.queue[a]["title"], a_pos=a + 1, b=state.queue[b]["title"], b_pos=b + 1)
            )
        except ValueError:
            await message.channel.send(t(gid, "invalid_number"))

    # --- /ping ---
    elif _match_command(content, "//ping"):
        latency_ms = round(client.latency * 1000)
        voice_info = ""
        state = music_states.get(gid)
        if state and state.voice_client and state.voice_client.is_connected():
            voice_latency = state.voice_client.latency
            if voice_latency:
                voice_info = t(gid, "voice_latency", voice=round(voice_latency * 1000))
        await message.channel.send(t(gid, "ping_msg", gateway=latency_ms) + voice_info)

    # --- /filters ---
    elif _match_command(content, "//filters"):
        state = get_music_state(gid)
        embed = build_filters_embed(state, gid)
        view = FilterSelectView(gid)
        await message.channel.send(embed=embed, view=view)

    # --- /bass ---
    elif _match_command(content, "//bass"):
        state = get_music_state(gid)
        cur = state.audio_filters.get("bass_boost", 0)
        state.audio_filters["bass_boost"] = (cur + 1) % 4
        level = state.audio_filters["bass_boost"]
        level_names = {0: "off", 1: "light", 2: "medium", 3: "heavy"}
        if state.voice_client and (state.voice_client.is_playing() or state.voice_client.is_paused()):
            pos = state.get_playback_position()
            await restart_playback_at_position(gid, pos, state)
        await message.channel.send(t(gid, "bass_boost_set", level=t(gid, f"bass_level_{level_names[level]}")))

    # --- /nightcore ---
    elif _match_command(content, "//nightcore"):
        state = get_music_state(gid)
        playing = state.voice_client and (state.voice_client.is_playing() or state.voice_client.is_paused())
        pos = state.get_playback_position() if playing else 0.0
        state.audio_filters["nightcore"] = not state.audio_filters["nightcore"]
        state.audio_filters["vaporwave"] = False
        key = "nightcore_on" if state.audio_filters["nightcore"] else "nightcore_off"
        if playing:
            await restart_playback_at_position(gid, pos, state)
        await message.channel.send(t(gid, key))

    # --- /vaporwave ---
    elif _match_command(content, "//vaporwave"):
        state = get_music_state(gid)
        playing = state.voice_client and (state.voice_client.is_playing() or state.voice_client.is_paused())
        pos = state.get_playback_position() if playing else 0.0
        state.audio_filters["vaporwave"] = not state.audio_filters["vaporwave"]
        state.audio_filters["nightcore"] = False
        key = "vaporwave_on" if state.audio_filters["vaporwave"] else "vaporwave_off"
        if playing:
            await restart_playback_at_position(gid, pos, state)
        await message.channel.send(t(gid, key))

    # --- /ask ---
    elif _match_command(content, "//ask"):
        args = content.split(maxsplit=1)
        if len(args) < 2:
            await message.channel.send(t(gid, "ask_usage"))
            return

        if not anthropic_client:
            await message.channel.send(t(gid, "ask_not_configured"))
            return

        # Check daily usage limit
        allowed, used, limit = _check_ask_limit(message.author.id)
        if not allowed:
            await message.channel.send(t(gid, "ask_limit_hit", used=used, max=limit))
            return

        query = args[1]
        thinking_msg = await message.channel.send(t(gid, "ask_thinking"))

        try:
            response = await anthropic_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=_build_system_prompt(gid),
                messages=[{"role": "user", "content": query}],
            )
            reply = response.content[0].text
            if len(reply) > 1900:
                reply = reply[:1900] + "..."
            # Append usage counter
            footer = f"\n-# {t(gid, 'ask_remaining', used=used, max=limit)}"
            if len(reply) + len(footer) <= 2000:
                reply += footer
            await thinking_msg.edit(content=reply)
        except Exception as exc:
            logger.error("Claude API error: %s", exc)
            await thinking_msg.edit(content=t(gid, "ask_error"))

    # --- /personality ---
    elif _match_command(content, "//personality"):
        args = content.split(maxsplit=1)
        if len(args) < 2:
            current = get_personality(gid)
            truncated = current[:300] + "..." if len(current) > 300 else current
            await message.channel.send(t(gid, "personality_current", text=truncated))
            return

        new_text = args[1].strip()
        if new_text.lower() in ("reset", "default"):
            reset_personality(gid)
            await message.channel.send(t(gid, "personality_reset"))
        elif len(new_text) > 500:
            await message.channel.send(t(gid, "personality_too_long"))
        else:
            set_personality(gid, new_text)
            await message.channel.send(t(gid, "personality_set", text=new_text))

    # --- /lang ---
    elif _match_command(content, "//lang"):
        args = content.split()
        if len(args) < 2:
            current = get_lang(gid)
            lang_name = SUPPORTED_LANGS.get(current, current)
            await message.channel.send(t(gid, "lang_current", lang=lang_name))
            return
        new_lang = args[1].lower()
        if new_lang not in SUPPORTED_LANGS:
            await message.channel.send(t(gid, "lang_invalid"))
            return
        set_lang(gid, new_lang)
        await message.channel.send(t(gid, "lang_set", lang=SUPPORTED_LANGS[new_lang]))

    # --- /ban (owner only) ---
    elif _match_command(content, "//ban"):
        if message.author.id != OWNER_ID:
            return
        if not message.mentions:
            await message.channel.send(t(gid, "ban_usage"))
            return
        target = message.mentions[0]
        if target.id == OWNER_ID:
            return
        _bans[target.id] = None
        _timeouts.pop(target.id, None)
        _save_bans()
        msg = await message.channel.send(t(gid, "ban_done", user=target.display_name))
        _auto_delete(msg, 5)

    # --- /unban (owner only) ---
    elif _match_command(content, "//unban"):
        if message.author.id != OWNER_ID:
            return
        if not message.mentions:
            await message.channel.send(t(gid, "unban_usage"))
            return
        target = message.mentions[0]
        removed = target.id in _bans or target.id in _timeouts
        _bans.pop(target.id, None)
        _timeouts.pop(target.id, None)
        _save_bans()
        key = "unban_done" if removed else "unban_not_banned"
        msg = await message.channel.send(t(gid, key, user=target.display_name))
        _auto_delete(msg, 5)

    # --- /timeout (owner only) ---
    elif _match_command(content, "//timeout"):
        if message.author.id != OWNER_ID:
            return
        args = content.split()
        if len(args) < 2 or not message.mentions:
            await message.channel.send(t(gid, "timeout_usage"))
            return
        target = message.mentions[0]
        if target.id == OWNER_ID:
            return
        duration_str = args[-1] if args[-1] != message.mentions[0].mention else "10m"
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            unit = duration_str[-1].lower()
            if unit in multipliers:
                seconds = int(duration_str[:-1]) * multipliers[unit]
            else:
                seconds = int(duration_str) * 60
        except (ValueError, IndexError):
            await message.channel.send(t(gid, "timeout_invalid"))
            return
        _timeouts[target.id] = time.time() + seconds
        _bans.pop(target.id, None)
        _save_bans()
        msg = await message.channel.send(t(gid, "timeout_done", user=target.display_name, duration=duration_str))
        _auto_delete(msg, 5)

    # --- /untimeout (owner only) ---
    elif _match_command(content, "//untimeout"):
        if message.author.id != OWNER_ID:
            return
        if not message.mentions:
            await message.channel.send(t(gid, "untimeout_usage"))
            return
        target = message.mentions[0]
        removed = target.id in _timeouts
        _timeouts.pop(target.id, None)
        _save_bans()
        key = "untimeout_done" if removed else "untimeout_not_timed_out"
        msg = await message.channel.send(t(gid, key, user=target.display_name))
        _auto_delete(msg, 5)

    # --- /restart (owner only) ---
    elif _match_command(content, "//restart"):
        if message.author.id != OWNER_ID:
            return
        await message.channel.send(t(gid, "restarting"))
        await _graceful_restart()

    # --- /shutdown (owner only) ---
    elif _match_command(content, "//shutdown"):
        if message.author.id != OWNER_ID:
            return
        await message.channel.send(t(gid, "shutting_down"))
        await shutdown()

    # --- /log (owner only, sent via DM) ---
    elif _match_command(content, "//log"):
        if message.author.id != OWNER_ID:
            return
        args = content.split()
        count = 20
        if len(args) >= 2:
            try:
                count = min(int(args[1]), 60)
            except ValueError:
                pass
        lines = list(_ring_handler.buffer)[-count:]
        try:
            dm = await message.author.create_dm()
            if not lines:
                await dm.send(t(gid, "log_empty"))
            else:
                text = "\n".join(lines)
                if len(text) > 1900:
                    text = text[-1900:]
                await dm.send(f"```\n{text}\n```")
            msg = await message.channel.send(t(gid, "log_sent_dm"))
            _auto_delete(msg, 3)
        except discord.Forbidden:
            await message.channel.send(t(gid, "log_dm_failed"))

    # --- /help ---
    elif _match_command(content, "//help"):
        args = content.split()
        # Sub-help: /help <topic>
        if len(args) >= 2:
            topic = args[1].lower().lstrip("/")
            await _send_help_topic(message.channel, topic, gid)
        else:
            await _send_help_overview(message.channel, gid)


async def _send_help_overview(channel, guild_id: int):
    """Send the main help embed with all command categories."""
    embed = Embed(
        title=t(guild_id, "help_title"),
        description=t(guild_id, "help_description"),
        color=Color.purple(),
    )

    embed.add_field(
        name=t(guild_id, "help_cat_playback"),
        value=t(guild_id, "help_cat_playback_val"),
        inline=False,
    )

    embed.add_field(
        name=t(guild_id, "help_cat_queue"),
        value=t(guild_id, "help_cat_queue_val"),
        inline=False,
    )

    embed.add_field(
        name=t(guild_id, "help_cat_settings"),
        value=t(guild_id, "help_cat_settings_val"),
        inline=False,
    )

    embed.add_field(
        name=t(guild_id, "help_cat_filters"),
        value=t(guild_id, "help_cat_filters_val"),
        inline=False,
    )

    embed.add_field(
        name=t(guild_id, "help_cat_utility"),
        value=t(guild_id, "help_cat_utility_val"),
        inline=False,
    )

    embed.add_field(
        name=t(guild_id, "help_cat_tips"),
        value=t(guild_id, "help_cat_tips_val"),
        inline=False,
    )

    embed.set_footer(text=t(guild_id, "help_footer"))
    await channel.send(embed=embed)


async def _send_help_topic(channel, topic: str, guild_id: int):
    """Send detailed help for a specific command or category."""
    if topic in _HELP_TOPIC_KEYS:
        title_key, body_key = _HELP_TOPIC_KEYS[topic]
        embed = Embed(
            title=t(guild_id, title_key),
            description=t(guild_id, body_key),
            color=Color.purple(),
        )
        embed.set_footer(text=t(guild_id, "help_topic_footer"))
        await channel.send(embed=embed)
    else:
        suggestions = ", ".join(f"`{k}`" for k in _HELP_VISIBLE_TOPICS)
        await channel.send(
            embed=create_embed(
                t(guild_id, "help_unknown_topic"),
                t(guild_id, "help_unknown_body", topic=topic, topics=suggestions),
                Color.orange(),
            )
        )


# ---------------------------------------------------------------------------
# Shutdown
# ---------------------------------------------------------------------------


_shutting_down = False

async def shutdown():
    global _shutting_down
    if _shutting_down:
        return
    _shutting_down = True
    logger.info("Shutting down...")
    for guild_id, state in list(music_states.items()):
        try:
            if state._current_view is not None:
                state._current_view.stop()
                state._current_view = None
            if state.now_playing_updater and not state.now_playing_updater.done():
                state.now_playing_updater.cancel()
            if state.voice_client and state.voice_client.is_connected():
                await state.voice_client.disconnect()
        except Exception:
            pass
    await client.close()


if __name__ == "__main__":
    try:
        client.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        asyncio.run(shutdown())
    except Exception as exc:
        logger.critical("Fatal error: %s", exc)
        raise

    # Restart the process if an auto-update was applied
    if _restart_pending:
        logger.info("Restarting bot process after yt-dlp update...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
