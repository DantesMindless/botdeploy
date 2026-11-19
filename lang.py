"""
Multilingual string definitions for Discord Music Bot.
Languages: English (en), Ukrainian (uk), Russian (ru).

Usage in bot.py:
    from lang import t, SUPPORTED_LANGS
    t(guild_id, "paused")           -> "Paused" / "Призупинено" / ...
    t(guild_id, "volume_set", vol=50) -> "Volume set to **50%**"
"""

import json
from pathlib import Path

SUPPORTED_LANGS = {
    "en": "🇬🇧 English",
    "ua": "🇺🇦 Українська",
    "ru": "🦅🦅 Кацапський",
}

DEFAULT_LANG = "en"

_LANG_FILE = Path(__file__).parent / "lang_prefs.json"
_guild_langs: dict[str, str] = {}


def _load():
    global _guild_langs
    if _LANG_FILE.exists():
        try:
            with open(_LANG_FILE, "r", encoding="utf-8") as f:
                _guild_langs = json.load(f)
        except Exception:
            _guild_langs = {}


def _save():
    with open(_LANG_FILE, "w", encoding="utf-8") as f:
        json.dump(_guild_langs, f)


def get_lang(guild_id: int) -> str:
    return _guild_langs.get(str(guild_id), DEFAULT_LANG)


def set_lang(guild_id: int, lang: str):
    _guild_langs[str(guild_id)] = lang
    _save()


def t(guild_id: int, key: str, **kw) -> str:
    """Translate a string key for the given guild's language."""
    lang = get_lang(guild_id)
    table = S.get(lang, S[DEFAULT_LANG])
    text = table.get(key) or S[DEFAULT_LANG].get(key) or key
    return text.format(**kw) if kw else text


_load()


# ==========================================================================
# ALL TRANSLATABLE STRINGS
# ==========================================================================

S: dict[str, dict[str, str]] = {}

# --------------------------------------------------------------------------
# ENGLISH
# --------------------------------------------------------------------------

S["en"] = {
    # -- General guards --
    "need_voice":        "❌ You need to be in a voice channel!",
    "need_bot_channel":  "❌ You need to be in the bot's voice channel!",
    "session_expired":   "⚠️ This player session has expired. Use `//play` to start a new one, or ➕ to add a song.",
    "need_same_channel": "❌ You need to be in the same voice channel as the bot!",

    # -- Playback --
    "provide_song":    "❌ Please provide a song name or URL.",
    "searching":       "🔍 Searching...",
    "song_not_found":  "❌ Could not find that song. Try a different search.",
    "nothing_playing": "❌ Nothing is playing",
    "nothing_paused":  "❌ Nothing is paused",
    "not_connected":   "❌ Not connected to voice",
    "paused":          "⏸️ Paused",
    "resumed":         "▶️ Resumed",
    "skipped":         "⏭️ Skipped",
    "stopped":         "⏹️ Stopped and disconnected",

    # -- Queue --
    "queue_full":          "❌ Queue is full ({max} tracks max).",
    "queue_empty":         "📭 Queue is empty",
    "queue_already_empty": "❌ Queue is already empty",
    "playlist_added":      "📝 Playlist Added",
    "playlist_added_desc": "Added **{count}** tracks to the queue",
    "added_to_queue":      "Added to Queue",
    "added_to_top":        "Added to Top of Queue",
    "now_playing":         "Now Playing",
    "up_next":             "Up Next",
    "songs_in_queue":      "{count} song(s) in queue",
    "up_next_count":       "Up Next ({count} songs)",
    "music_queue":         "📜 Music Queue",
    "and_more":            "*...and {count} more*",
    "position":            "Position",
    "next_up":             "#1 (next up)",

    # -- Now Playing embed fields --
    "channel_field": "Channel",
    "duration_field": "Duration",
    "views_field":    "Views",
    "queue_field":    "Queue",
    "volume_field":   "Volume",
    "loop_field":     "Loop",
    "powered_by":     "Powered by yt-dlp",

    # -- Volume --
    "volume_current": "🔊 Volume: **{vol}%**",
    "volume_set":     "🔊 Volume set to **{vol}%**",
    "volume_range":   "❌ Volume must be between 0 and 200",
    "invalid_volume": "❌ Invalid volume value",

    # -- Loop --
    "loop_off":      "➡️ Loop: **Off**",
    "loop_single":   "🔂 Loop: **Single**",
    "loop_queue":    "🔁 Loop: **Queue**",
    "loop_shuffle":  "🔀 Loop: **Shuffle**",
    "invalid_loop":  "❌ Invalid loop mode. Use: `off`, `single`, `queue`, or `shuffle`",

    # -- Shuffle / Clear / Remove --
    "shuffled":          "🔀 Shuffled {count} songs",
    "need_2_songs":      "❌ Need at least 2 songs in queue to shuffle",
    "cleared":           "🗑️ Cleared {count} songs from queue",
    "removed":           "✅ Removed: **{title}**",
    "invalid_position":  "❌ Invalid position",
    "invalid_number":    "❌ Invalid position number",

    # -- Skipto --
    "skipto_usage":   "❌ Usage: `//skipto <position>` (e.g. `//skipto 3`)",
    "skipto_invalid": "❌ Invalid position. Queue has {count} songs.",
    "skipto_msg":     "⏭️ Skipped {count} song(s), jumping to **{title}**",

    # -- Replay --
    "replay_msg":        "🔄 Replaying current track",
    "nothing_to_replay": "❌ Nothing is playing to replay",

    # -- Playtop --
    "playtop_usage":       "❌ Usage: `//playtop <song/url>`",
    "playtop_no_playlist": "❌ `//playtop` works with single songs, not playlists. Use `//play` instead.",

    # -- Swap --
    "swap_usage":    "❌ Usage: `//swap <pos1> <pos2>` (e.g. `//swap 1 3`)",
    "swap_range":    "❌ Positions must be between 1 and {count}",
    "swap_same":     "❌ Positions must be different",
    "swapped":       "🔄 Swapped **{a}** (#{a_pos}) with **{b}** (#{b_pos})",

    # -- Move --
    "moved":              "🔀 Moved to **{channel}**",
    "already_in_channel": "❌ Already in your channel!",
    "bot_not_in_voice":   "❌ Bot is not in a voice channel",

    # -- Ping --
    "ping_msg":       "🏓 Pong! Gateway latency: **{gateway}ms**",
    "voice_latency":  "\nVoice latency: **{voice}ms**",

    # -- Search --
    "search_usage":   "❌ Usage: //search <query>",
    "search_results": "🔍 Search Results: {query}",
    "no_results":     "❌ No results found",

    # -- Filters --
    "audio_filters":  "🎛️ Audio Filters",
    "filters_cmds":   "Commands",
    "filters_desc":   "`//bass` — Toggle bass boost\n`//nightcore` — Toggle nightcore\n`//vaporwave` — Toggle vaporwave",
    "active":         "✅ Active",
    "inactive":       "❌ Inactive",
    "bass_on":        "🔊 Bass boost **enabled**",
    "bass_off":       "🔊 Bass boost **disabled**",
    "nightcore_on":   "⚡ Nightcore **enabled**",
    "nightcore_off":  "⚡ Nightcore **disabled**",
    "vaporwave_on":   "🌊 Vaporwave **enabled**",
    "vaporwave_off":  "🌊 Vaporwave **disabled**",
    "speed":          "Speed",
    "progress":       "Progress",
    "filters_active": "Filters",
    "filters_restart_note": "Changes apply immediately from the current position.",
    "filters_next_note":    "Filters will apply when a track starts playing.",
    "nightcore_vaporwave_exclusive": "Nightcore and Vaporwave can't be used together.",

    # -- Errors --
    "error":              "❌ Error",
    "connection_failed":  "❌ Connection Failed",
    "playback_error":     "❌ Playback Error",
    "playback_error_desc": "Failed to play: **{title}**\nSkipping to next track...",
    "search_error":       "❌ Search Error",

    # -- Language --
    "lang_set":     "🌐 Language set to **{lang}**",
    "lang_current": "🌐 Current language: **{lang}**\nUse `//lang <en|ua|ru>` to change.",
    "lang_invalid": "❌ Invalid language. Available: `en` 🇬🇧 English, `ua` 🇺🇦 Українська, `ru` 🦅🦅 Кацапський",

    # -- Remove usage --
    "remove_usage": "❌ Usage: `//remove <position>`",

    # -- AI Assistant --
    "ask_usage":          "❌ Usage: `//ask <question>`",
    "ask_thinking":       "🤔 Thinking...",
    "ask_error":          "❌ Could not get a response. Please try again.",
    "ask_not_configured": "❌ AI assistant is not configured.",
    "ask_limit_hit":      "❌ Daily limit reached ({used}/{max}). Resets at midnight UTC.",
    "ask_remaining":      "💬 AI response ({used}/{max} daily uses)",

    # -- Personality --
    "personality_current":  "🎭 Current personality:\n> {text}\n\nUse `//personality <text>` to change or `//personality reset` for default.",
    "personality_set":      "🎭 Personality updated:\n> {text}",
    "personality_reset":    "🎭 Personality reset to default.",
    "personality_too_long": "❌ Personality text is too long (500 characters max).",

    # -- AI DJ --
    "dj_usage":      "❌ Usage: `//dj <mood, artist, or genre>`\nExamples: `//dj chill vibes` · `//dj like Deftones` · `//dj 90s hip hop`",
    "dj_thinking":   "🎧 AI DJ is picking songs...",
    "dj_error":      "❌ AI DJ couldn't generate a playlist. Try again.",
    "dj_added":      "🎧 AI DJ queued {count} songs",
    "dj_no_results": "❌ Couldn't find any of the suggested songs on YouTube.",

    # -- Vibe Check --
    "vibe_thinking":        "🎵 Analyzing the vibe...",
    "vibe_nothing_playing": "❌ Nothing is playing. Queue some songs first!",

    # -- Listening History --
    "history_empty":            "📭 No listening history yet. Play some songs first!",
    "history_title":            "📜 Listening History",
    "history_total":            "songs total",
    "history_play_placeholder": "🔁 Replay a song from history...",
    "history_profile_btn":      "🧠 AI Taste Profile",
    # -- UI: Player buttons & labels --
    "btn_prev":          "Prev",
    "btn_rewind":        "-15s",
    "btn_pause":         "Pause",
    "btn_resume":        "Resume",
    "btn_forward":       "+15s",
    "btn_skip":          "Skip",
    "btn_add":           "Add",
    "btn_loop_off":      "Loop: Off",
    "btn_loop_single":   "Loop: One",
    "btn_loop_queue":    "Loop: All",
    "btn_loop_shuffle":  "Shuffle",
    "btn_remove":        "Remove",
    "btn_clear":         "Clear",
    "btn_stop":          "Stop",
    "btn_add_song":      "Add Song",
    "btn_disconnect":    "Disconnect",
    "bass_off_label":    "Bass: Off",
    "bass_light_label":  "Bass: Light",
    "bass_med_label":    "Bass: Med",
    "bass_heavy_label":  "Bass: Heavy",
    "btn_nightcore":     "Nightcore",
    "btn_vaporwave":     "Vaporwave",

    # -- UI: Dropdowns & placeholders --
    "vol_placeholder":       "Volume: {vol}%",
    "queue_placeholder":     "Queue: {played} played, {upcoming} upcoming",
    "queue_placeholder_short": "Queue: {upcoming} upcoming",
    "queue_now_playing":     "Now playing",
    "queue_played":          "Played",
    "queue_upcoming":        "Upcoming",
    "remove_placeholder":    "Select song to remove...",

    # -- UI: Modal --
    "modal_add_song":        "Add Song",
    "modal_song_label":      "Song name or URL",
    "modal_song_placeholder": "e.g. Nirvana - Smells Like Teen Spirit",

    # -- UI: Player idle --
    "player_title":          "Music Player",
    "player_idle_desc":      "Click **+ Add** to queue songs",

    # -- UI: Ephemeral messages --
    "added_tracks":          "Added **{count}** tracks to queue",
    "added_song":            "Added **{title}** to queue",
    "nothing_to_remove":     "Nothing to remove.",
    "select_to_remove":      "Select a song to remove:",
    "song_unavailable":      "Song no longer available.",
    "song_not_in_queue":     "Song no longer in queue.",
    "song_not_in_history":   "Song no longer in history.",
    "removed_from_queue":    "Removed **{title}** from queue.",
    "removed_from_history":  "Removed **{title}** from history.",
    "remove_upcoming_desc":  "Upcoming - {dur}",
    "remove_played_desc":    "Played - {dur}",
    "remove_nothing_label":  "Nothing to remove",
    "remove_select_placeholder": "Select song to remove...",

    # -- Filters (command output) --
    "bass_boost_set":        "Bass boost: **{level}**",
    "bass_level_off":        "off",
    "bass_level_light":      "light",
    "bass_level_medium":     "medium",
    "bass_level_heavy":      "heavy",

    # -- Filter dropdown labels (//filters command) --
    "filter_bass_light":     "Bass: Light",
    "filter_bass_medium":    "Bass: Medium",
    "filter_bass_heavy":     "Bass: Heavy",
    "filter_nightcore":      "Nightcore",
    "filter_vaporwave":      "Vaporwave",
    "filter_bass_light_desc": "+5dB low frequencies",
    "filter_bass_med_desc":  "+10dB low frequencies",
    "filter_bass_heavy_desc": "+15dB low frequencies",
    "filter_nc_desc":        "1.25x speed, higher pitch",
    "filter_vw_desc":        "0.8x speed, lower pitch",
    "filter_placeholder":    "Audio filters...",

    # -- Owner: Ban / Timeout --
    "ban_usage":             "Usage: `//ban @user`",
    "ban_done":              "**{user}** has been banned from using the bot.",
    "unban_usage":           "Usage: `//unban @user`",
    "unban_done":            "**{user}** has been unbanned.",
    "unban_not_banned":      "**{user}** is not banned.",
    "timeout_usage":         "Usage: `//timeout @user <duration>` (e.g. 10m, 1h, 1d)",
    "timeout_invalid":       "Invalid duration. Use a number + s/m/h/d (e.g. `30m`, `2h`).",
    "timeout_done":          "**{user}** timed out for **{duration}**.",
    "untimeout_usage":       "Usage: `//untimeout @user`",
    "untimeout_done":        "**{user}** timeout removed.",
    "untimeout_not_timed_out": "**{user}** is not timed out.",
    "restarting":            "Restarting bot...",
    "shutting_down":         "Shutting down...",
    "log_empty":             "No log entries yet.",
    "log_sent_dm":           "Logs sent to your DMs.",
    "log_dm_failed":         "Couldn't DM you — check your privacy settings.",

    # =======================================================================
    # HELP — Overview
    # =======================================================================
    "help_title":       "🎵 Music Bot — Command Reference",
    "help_description": (
        "A full-featured music bot with an interactive Spotify-style player, "
        "YouTube support, audio filters, and queue management.\n\n"
        "**Tip:** Use `//start` to open the player without typing commands!\n"
        "Or `//help <topic>` for detailed info on a category."
    ),
    "help_cat_playback":       "▶️ Playback",
    "help_cat_playback_val": (
        "`//start` — Open the interactive player (add songs via button)\n"
        "`//play <song/url>` — Play a song, search term, or playlist\n"
        "`//playtop <song/url>` — Add a song to the **front** of the queue\n"
        "`//search <query>` — Search YouTube and browse results\n"
        "`//pause` — Pause the current track\n"
        "`//resume` — Resume paused playback\n"
        "`//skip` — Skip to the next song in queue\n"
        "`//replay` — Restart the current track from the beginning\n"
        "`//stop` — Stop playback, clear queue, and disconnect"
    ),
    "help_cat_queue":          "📝 Queue Management",
    "help_cat_queue_val": (
        "The player has a **queue dropdown** showing played, current, and upcoming songs.\n"
        "Click any song in the dropdown to jump to it.\n\n"
        "`//queue` or `//q` — View the current queue (now playing + next 10)\n"
        "`//shuffle` — Randomize the order of queued songs\n"
        "`//clear` — Remove all songs from the queue\n"
        "`//remove <position>` — Remove a specific song (e.g. `//remove 3`)\n"
        "`//skipto <position>` — Jump to a queue position\n"
        "`//swap <pos1> <pos2>` — Swap two songs in the queue"
    ),
    "help_cat_settings":       "🎛️ Playback Settings",
    "help_cat_settings_val": (
        "All settings are available as **buttons and dropdowns** in the player.\n\n"
        "`//volume <0-200>` — Set volume (100 = normal, 200 = 2x boost)\n"
        "`//loop` — Cycle: off → single → queue → shuffle\n"
        "`//move` — Move the bot to your current voice channel"
    ),
    "help_cat_filters":        "🎚️ Audio Filters",
    "help_cat_filters_val": (
        "Select filters from the **dropdown in the player** — they apply instantly!\n\n"
        "`//bass` — Toggle bass boost (+10dB low frequencies)\n"
        "`//nightcore` — Toggle nightcore (25% faster, higher pitch)\n"
        "`//vaporwave` — Toggle vaporwave (20% slower, lower pitch)\n"
        "*Nightcore and vaporwave are mutually exclusive; bass stacks with either.*"
    ),
    "help_cat_utility":        "🔧 Utility & AI",
    "help_cat_utility_val": (
        "`//dj <mood/artist/genre>` — AI picks and queues 5 songs matching your vibe\n"
        "`//vibe` — AI analyzes your current queue's mood and suggests more\n"
        "`//history` — View listening history by user, replay songs, AI taste profile\n"
        "`//ask <anything>` — Ask AI or tell it to control the bot (context-aware)\n"
        "`//personality <text>` — Customize the AI's personality for this server\n"
        "`//ping` — Check bot gateway and voice connection latency\n"
        "`//lang <en|ua|ru>` — Change bot language for this server\n"
        "`//help` — Show this overview"
    ),
    "help_cat_tips":           "💡 Good to Know",
    "help_cat_tips_val": (
        "• **Interactive player:** Use `//start` — add songs, skip, seek, filter, all from buttons\n"
        "• **Queue limit:** 100 songs max\n"
        "• **Auto-disconnect:** 5 min idle with no queue, or 1 min if alone in channel\n"
        "• **Voice channel required:** You must be in the bot's voice channel to use controls\n"
        "• **Cooldown:** 2 second cooldown between commands to prevent spam\n"
        "• **Supported sources:** YouTube links, playlists, and search terms"
    ),
    "help_footer": "//help <topic> for details",

    # =======================================================================
    # HELP — Per-topic detailed pages
    # =======================================================================
    "help_play_title": "▶️ //play — Play Music",
    "help_play_body": (
        "**Usage:** `//play <song name or YouTube URL>`\n\n"
        "**Examples:**\n"
        "• `//play never gonna give you up` — Search and play\n"
        "• `//play https://youtube.com/watch?v=...` — Play a specific video\n"
        "• `//play https://youtube.com/playlist?list=...` — Queue an entire playlist\n\n"
        "**How it works:**\n"
        "1. If you're not in a voice channel, the bot will tell you to join one\n"
        "2. If the bot isn't connected, it joins your voice channel\n"
        "3. The song is added to the end of the queue\n"
        "4. If nothing is playing, playback starts immediately\n\n"
        "**See also:** `//playtop` (add to front) · `//search` (browse results)"
    ),
    "help_playtop_title": "⏫ //playtop — Play Next",
    "help_playtop_body": (
        "**Usage:** `//playtop <song name or URL>`\n\n"
        "Works like `//play`, but inserts the song at **position #1** in the queue "
        "so it plays next after the current track.\n\n"
        "**Note:** Only works with single songs, not playlists."
    ),
    "help_search_title": "🔍 //search — Search YouTube",
    "help_search_body": (
        "**Usage:** `//search <query>`\n\n"
        "**Example:** `//search lofi hip hop radio`\n\n"
        "Returns the top 5 YouTube results with title, channel, and duration. "
        "Copy the `//play` command shown under each result to queue it."
    ),
    "help_pause_title": "⏸️ //pause & //resume",
    "help_pause_body": (
        "**`//pause`** — Pause the currently playing track.\n"
        "**`//resume`** — Resume a paused track.\n\n"
        "You must be in the bot's voice channel to use these."
    ),
    "help_skip_title": "⏭️ //skip — Skip Track",
    "help_skip_body": (
        "**Usage:** `//skip`\n\n"
        "Skips the current song and plays the next one in queue.\n"
        "If loop mode is set to `single`, skip will temporarily disable it for one track.\n\n"
        "**See also:** `//skipto` (jump to a position) · `//replay` (restart current)"
    ),
    "help_skipto_title": "⏭️ //skipto — Jump in Queue",
    "help_skipto_body": (
        "**Usage:** `//skipto <position>`\n\n"
        "**Example:** `//skipto 5` — Skips songs 1-4 and plays song #5\n\n"
        "All songs before the target position are discarded from the queue."
    ),
    "help_replay_title": "🔄 //replay — Restart Track",
    "help_replay_body": (
        "**Usage:** `//replay`\n\n"
        "Restarts the currently playing song from the beginning. "
        "Works regardless of loop mode."
    ),
    "help_stop_title": "⏹️ //stop — Stop Everything",
    "help_stop_body": (
        "**Usage:** `//stop`\n\n"
        "Stops playback, clears the entire queue, resets loop mode, "
        "and disconnects the bot from voice."
    ),
    "help_queue_title": "📜 //queue — View Queue",
    "help_queue_body": (
        "**Usage:** `//queue` or `//q`\n\n"
        "Shows the currently playing song and the next 10 songs in queue, "
        "along with volume and loop status.\n\n"
        "**See also:** `//np` (detailed current track info)"
    ),
    "help_np_title": "🎵 //nowplaying — Current Track",
    "help_np_body": (
        "**Usage:** `//np` or `//nowplaying`\n\n"
        "Shows detailed info about the current track: title, channel, "
        "duration, view count, thumbnail, queue size, volume, and loop mode."
    ),
    "help_shuffle_title": "🔀 //shuffle — Randomize Queue",
    "help_shuffle_body": (
        "**Usage:** `//shuffle`\n\n"
        "Randomly reorders all songs in the queue. "
        "The currently playing song is not affected.\n"
        "Requires at least 2 songs in queue."
    ),
    "help_clear_title": "🗑️ //clear — Clear Queue",
    "help_clear_body": (
        "**Usage:** `//clear`\n\n"
        "Removes all songs from the queue. The currently playing song continues "
        "until it ends (use `//stop` to also stop playback)."
    ),
    "help_remove_title": "❌ //remove — Remove a Song",
    "help_remove_body": (
        "**Usage:** `//remove <position>`\n\n"
        "**Example:** `//remove 3` — Removes the 3rd song from the queue\n\n"
        "Use `//queue` first to see positions."
    ),
    "help_swap_title": "🔄 //swap — Swap Songs",
    "help_swap_body": (
        "**Usage:** `//swap <pos1> <pos2>`\n\n"
        "**Example:** `//swap 1 5` — Swaps the 1st and 5th songs in queue\n\n"
        "Use `//queue` first to see positions."
    ),
    "help_volume_title": "🔊 //volume — Volume Control",
    "help_volume_body": (
        "**Usage:**\n"
        "• `//volume` — Show current volume\n"
        "• `//volume 50` — Set to 50%\n"
        "• `//volume 150` — Set to 150% (amplified)\n\n"
        "**Range:** 0 (mute) to 200 (2x amplification).\n"
        "Default is 50%. Changes apply immediately to the current track."
    ),
    "help_loop_title": "🔁 //loop — Loop Modes",
    "help_loop_body": (
        "**Usage:**\n"
        "• `//loop` — Cycle through modes: off → single → queue\n"
        "• `//loop off` — Disable looping\n"
        "• `//loop single` — Repeat the current track endlessly\n"
        "• `//loop queue` — When the queue ends, start over from the beginning\n\n"
        "**Aliases:** `off`/`none`/`no`, `single`/`one`/`song`, `queue`/`all`\n\n"
        "**Note:** `//skip` temporarily overrides single-loop for one track."
    ),
    "help_move_title": "🔀 //move — Move Bot",
    "help_move_body": (
        "**Usage:** `//move`\n\n"
        "Moves the bot to your current voice channel. Useful when you switch "
        "channels without wanting to stop playback."
    ),
    "help_filters_title": "🎚️ Audio Filters",
    "help_filters_body": (
        "**Commands:**\n"
        "• `//filters` — View which filters are currently active\n"
        "• `//bass` — Toggle bass boost (+10dB low frequencies)\n"
        "• `//nightcore` — Toggle nightcore (1.25x speed, higher pitch)\n"
        "• `//vaporwave` — Toggle vaporwave (0.8x speed, lower pitch)\n\n"
        "**Important notes:**\n"
        "• Filters apply to the **next** track, not the current one\n"
        "• Nightcore and vaporwave cancel each other (can't use both)\n"
        "• Bass boost stacks with either nightcore or vaporwave\n"
        "• All filters include audio normalization to prevent clipping"
    ),
    "help_ping_title": "🏓 //ping — Latency Check",
    "help_ping_body": (
        "**Usage:** `//ping`\n\n"
        "Shows the bot's gateway latency (connection to Discord) and voice "
        "latency (if connected to a voice channel)."
    ),
    "help_lang_title": "🌐 //lang — Language",
    "help_lang_body": (
        "**Usage:** `//lang <en|ua|ru>`\n\n"
        "Changes the bot's language for this server.\n"
        "• `en` — English\n"
        "• `ua` — Українська (Ukrainian)\n"
        "• `ru` — Кацапський (Russian)\n\n"
        "Language preference is saved per server."
    ),
    "help_ask_title": "🤖 //ask — AI Assistant & Operator",
    "help_ask_body": (
        "**Usage:** `//ask <question or command>`\n\n"
        "**Examples:**\n"
        "• `//ask What genre is this song?` — asks about what's playing\n"
        "• `//ask play something chill` — AI queues 5 chill songs\n"
        "• `//ask skip this and turn up the volume` — controls the bot\n"
        "• `//ask queue 5 songs like Deftones` — AI picks and queues songs\n"
        "• `//ask what's the vibe of this queue?` — analyzes the mood\n\n"
        "AI knows what's playing, what's in queue, volume, filters, and history.\n"
        "When you're in a voice channel, it can also control the bot for you.\n"
        "Daily usage limit applies per user."
    ),
    "help_personality_title": "🎭 //personality — AI Personality",
    "help_personality_body": (
        "**Usage:**\n"
        "• `//personality` — Show current AI personality\n"
        "• `//personality <text>` — Set a custom personality for this server\n"
        "• `//personality reset` — Reset to the default personality\n\n"
        "**Example:** `//personality You are a sarcastic pirate who only talks about sea shanties`\n\n"
        "The personality shapes how the AI responds to `//ask` questions.\n"
        "Max 500 characters. Saved per server."
    ),
    "help_dj_title": "🎧 //dj — AI DJ",
    "help_dj_body": (
        "**Usage:** `//dj <mood, artist, or genre>`\n\n"
        "**Examples:**\n"
        "• `//dj chill vibes for studying`\n"
        "• `//dj like Deftones`\n"
        "• `//dj 90s hip hop classics`\n"
        "• `//dj upbeat electronic workout`\n\n"
        "AI picks 5 songs matching your description and queues them.\n"
        "Works with moods, artists, genres, eras, or any combination.\n"
        "Uses one daily AI credit per use."
    ),
    "help_vibe_title": "🎵 //vibe — Queue Vibe Check",
    "help_vibe_body": (
        "**Usage:** `//vibe`\n\n"
        "AI analyzes what's currently playing and queued, describes the overall mood,\n"
        "and suggests songs that would fit the vibe.\n\n"
        "Takes into account the current track, play history, and upcoming queue.\n"
        "Uses one daily AI credit per use."
    ),
    "help_history_title": "📜 //history — Listening History",
    "help_history_body": (
        "**Usage:** `//history`\n\n"
        "Shows all songs played on this server, grouped by who queued them.\n"
        "Includes a dropdown to replay any song from history.\n\n"
        "**AI Taste Profile** button (appears with 5+ songs):\n"
        "Claude analyzes everyone's listening patterns and describes each user's taste.\n"
        "Uses one daily AI credit."
    ),
    "help_unknown_topic": "❓ Unknown Topic",
    "help_unknown_body":  "No help found for `{topic}`.\n\n**Available topics:**\n{topics}",
    "help_topic_footer":  "//help for full command list",
}


# --------------------------------------------------------------------------
# UKRAINIAN
# --------------------------------------------------------------------------

S["ua"] = {
    # -- Загальні --
    "need_voice":        "❌ Ви повинні бути в голосовому каналі!",
    "need_bot_channel":  "❌ Ви повинні бути в голосовому каналі бота!",
    "session_expired":   "⚠️ Ця сесія плеєра закінчилась. Використовуйте `//play` щоб почати нову, або ➕ щоб додати пісню.",
    "need_same_channel": "❌ Ви повинні бути в тому ж голосовому каналі, що й бот!",

    # -- Відтворення --
    "provide_song":    "❌ Будь ласка, вкажіть назву пісні або URL.",
    "searching":       "🔍 Шукаю...",
    "song_not_found":  "❌ Не вдалося знайти цю пісню. Спробуйте інший запит.",
    "nothing_playing": "❌ Нічого не відтворюється",
    "nothing_paused":  "❌ Нічого не призупинено",
    "not_connected":   "❌ Бот не підключений до голосового каналу",
    "paused":          "⏸️ Призупинено",
    "resumed":         "▶️ Відновлено",
    "skipped":         "⏭️ Пропущено",
    "stopped":         "⏹️ Зупинено та відключено",

    # -- Черга --
    "queue_full":          "❌ Черга заповнена (максимум {max} треків).",
    "queue_empty":         "📭 Черга порожня",
    "queue_already_empty": "❌ Черга вже порожня",
    "playlist_added":      "📝 Плейлист додано",
    "playlist_added_desc": "Додано **{count}** треків до черги",
    "added_to_queue":      "Додано до черги",
    "added_to_top":        "Додано на початок черги",
    "now_playing":         "Зараз грає",
    "up_next":             "Далі",
    "songs_in_queue":      "{count} пісень у черзі",
    "up_next_count":       "Далі ({count} пісень)",
    "music_queue":         "📜 Музична черга",
    "and_more":            "*...та ще {count}*",
    "position":            "Позиція",
    "next_up":             "#1 (наступна)",

    # -- Поля ембеду --
    "channel_field": "Канал",
    "duration_field": "Тривалість",
    "views_field":    "Перегляди",
    "queue_field":    "Черга",
    "volume_field":   "Гучність",
    "loop_field":     "Повтор",
    "powered_by":     "Працює на yt-dlp",

    # -- Гучність --
    "volume_current": "🔊 Гучність: **{vol}%**",
    "volume_set":     "🔊 Гучність встановлена на **{vol}%**",
    "volume_range":   "❌ Гучність повинна бути від 0 до 200",
    "invalid_volume": "❌ Невірне значення гучності",

    # -- Повтор --
    "loop_off":      "➡️ Повтор: **Вимкнено**",
    "loop_single":   "🔂 Повтор: **Один трек**",
    "loop_queue":    "🔁 Повтор: **Уся черга**",
    "loop_shuffle":  "🔀 Повтор: **Змішати**",
    "invalid_loop":  "❌ Невірний режим повтору. Використовуйте: `off`, `single` або `queue`",

    # -- Перемішати / Очистити / Видалити --
    "shuffled":          "🔀 Перемішано {count} пісень",
    "need_2_songs":      "❌ Потрібно щонайменше 2 пісні в черзі для перемішування",
    "cleared":           "🗑️ Видалено {count} пісень з черги",
    "removed":           "✅ Видалено: **{title}**",
    "invalid_position":  "❌ Невірна позиція",
    "invalid_number":    "❌ Невірний номер позиції",

    # -- Перехід --
    "skipto_usage":   "❌ Використання: `//skipto <позиція>` (напр. `//skipto 3`)",
    "skipto_invalid": "❌ Невірна позиція. У черзі {count} пісень.",
    "skipto_msg":     "⏭️ Пропущено {count} пісень, перехід до **{title}**",

    # -- Повтор треку --
    "replay_msg":        "🔄 Повторюю поточний трек",
    "nothing_to_replay": "❌ Нічого не відтворюється для повтору",

    # -- Playtop --
    "playtop_usage":       "❌ Використання: `//playtop <пісня/url>`",
    "playtop_no_playlist": "❌ `//playtop` працює тільки з окремими піснями, не з плейлистами. Використовуйте `//play`.",

    # -- Обмін --
    "swap_usage":    "❌ Використання: `//swap <поз1> <поз2>` (напр. `//swap 1 3`)",
    "swap_range":    "❌ Позиції повинні бути від 1 до {count}",
    "swap_same":     "❌ Позиції повинні бути різними",
    "swapped":       "🔄 Поміняно **{a}** (#{a_pos}) з **{b}** (#{b_pos})",

    # -- Переміщення --
    "moved":              "🔀 Переміщено до **{channel}**",
    "already_in_channel": "❌ Бот вже у вашому каналі!",
    "bot_not_in_voice":   "❌ Бот не підключений до голосового каналу",

    # -- Пінг --
    "ping_msg":       "🏓 Понг! Затримка шлюзу: **{gateway}мс**",
    "voice_latency":  "\nЗатримка голосу: **{voice}мс**",

    # -- Пошук --
    "search_usage":   "❌ Використання: //search <запит>",
    "search_results": "🔍 Результати пошуку: {query}",
    "no_results":     "❌ Нічого не знайдено",

    # -- Фільтри --
    "audio_filters":  "🎛️ Аудіо фільтри",
    "filters_cmds":   "Команди",
    "filters_desc":   "`//bass` — Підсилення басу\n`//nightcore` — Найткор\n`//vaporwave` — Вейпорвейв",
    "active":         "✅ Активний",
    "inactive":       "❌ Неактивний",
    "bass_on":        "🔊 Підсилення басу **увімкнено**",
    "bass_off":       "🔊 Підсилення басу **вимкнено**",
    "nightcore_on":   "⚡ Найткор **увімкнено**",
    "nightcore_off":  "⚡ Найткор **вимкнено**",
    "vaporwave_on":   "🌊 Вейпорвейв **увімкнено**",
    "vaporwave_off":  "🌊 Вейпорвейв **вимкнено**",
    "speed":          "Швидкість",
    "progress":       "Прогрес",
    "filters_active": "Фільтри",
    "filters_restart_note": "Зміни застосовуються одразу з поточної позиції.",
    "filters_next_note":    "Фільтри застосуються коли почнеться трек.",
    "nightcore_vaporwave_exclusive": "Найткор і Вейпорвейв не можуть працювати одночасно.",

    # -- Помилки --
    "error":              "❌ Помилка",
    "connection_failed":  "❌ Не вдалося підключитися",
    "playback_error":     "❌ Помилка відтворення",
    "playback_error_desc": "Не вдалося відтворити: **{title}**\nПерехід до наступного треку...",
    "search_error":       "❌ Помилка пошуку",

    # -- Мова --
    "lang_set":     "🌐 Мову змінено на **{lang}**",
    "lang_current": "🌐 Поточна мова: **{lang}**\nВикористовуйте `//lang <en|ua|ru>` для зміни.",
    "lang_invalid": "❌ Невірна мова. Доступні: `en` 🇬🇧 English, `ua` 🇺🇦 Українська, `ru` 🦅🦅 Кацапський",

    # -- Remove usage --
    "remove_usage": "❌ Використання: `//remove <позиція>`",

    # -- AI Асистент --
    "ask_usage":          "❌ Використання: `//ask <питання>`",
    "ask_thinking":       "🤔 Думаю...",
    "ask_error":          "❌ Не вдалося отримати відповідь. Спробуйте ще раз.",
    "ask_not_configured": "❌ AI асистент не налаштований.",
    "ask_limit_hit":      "❌ Денний ліміт вичерпано ({used}/{max}). Скидання опівночі UTC.",
    "ask_remaining":      "💬 AI відповідь ({used}/{max} денних запитів)",

    # -- Персональність --
    "personality_current":  "🎭 Поточна персональність:\n> {text}\n\nВикористовуйте `//personality <текст>` для зміни або `//personality reset` для стандартної.",
    "personality_set":      "🎭 Персональність оновлено:\n> {text}",
    "personality_reset":    "🎭 Персональність скинуто до стандартної.",
    "personality_too_long": "❌ Текст персональності занадто довгий (максимум 500 символів).",

    # -- AI DJ --
    "dj_usage":      "❌ Використання: `//dj <настрій, виконавець або жанр>`\nПриклади: `//dj чілл вайб` · `//dj як Deftones` · `//dj 90-ті хіп-хоп`",
    "dj_thinking":   "🎧 AI DJ підбирає пісні...",
    "dj_error":      "❌ AI DJ не зміг створити плейлист. Спробуйте ще раз.",
    "dj_added":      "🎧 AI DJ додав {count} пісень",
    "dj_no_results": "❌ Не вдалося знайти жодну з запропонованих пісень на YouTube.",

    # -- Vibe Check --
    "vibe_thinking":        "🎵 Аналізую вайб...",
    "vibe_nothing_playing": "❌ Нічого не грає. Спершу додайте пісні!",

    # -- Історія прослуховування --
    "history_empty":            "📭 Історія прослуховування порожня. Спершу зіграйте пісні!",
    "history_title":            "📜 Історія прослуховування",
    "history_total":            "пісень загалом",
    "history_play_placeholder": "🔁 Переграти пісню з історії...",
    "history_profile_btn":      "🧠 AI Смаковий профіль",
    # -- UI: Кнопки плеєра --
    "btn_prev":          "Назад",
    "btn_rewind":        "-15с",
    "btn_pause":         "Пауза",
    "btn_resume":        "Далі",
    "btn_forward":       "+15с",
    "btn_skip":          "Далі",
    "btn_add":           "Додати",
    "btn_loop_off":      "Повтор: Ні",
    "btn_loop_single":   "Повтор: Один",
    "btn_loop_queue":    "Повтор: Все",
    "btn_loop_shuffle":  "Змішати",
    "btn_remove":        "Видалити",
    "btn_clear":         "Очист.",
    "btn_stop":          "Стоп",
    "btn_add_song":      "Додати пісню",
    "btn_disconnect":    "Відключити",
    "bass_off_label":    "Бас: Ні",
    "bass_light_label":  "Бас: Легко",
    "bass_med_label":    "Бас: Серед.",
    "bass_heavy_label":  "Бас: Важко",
    "btn_nightcore":     "Найткор",
    "btn_vaporwave":     "Вейпорвейв",

    # -- UI: Випадаючі меню --
    "vol_placeholder":       "Гучність: {vol}%",
    "queue_placeholder":     "Черга: {played} відтворено, {upcoming} далі",
    "queue_placeholder_short": "Черга: {upcoming} далі",
    "queue_now_playing":     "Зараз грає",
    "queue_played":          "Відтворено",
    "queue_upcoming":        "Далі",
    "remove_placeholder":    "Оберіть пісню для видалення...",

    # -- UI: Модальне вікно --
    "modal_add_song":        "Додати пісню",
    "modal_song_label":      "Назва пісні або URL",
    "modal_song_placeholder": "напр. Nirvana - Smells Like Teen Spirit",

    # -- UI: Плеєр --
    "player_title":          "Музичний плеєр",
    "player_idle_desc":      "Натисніть **+ Додати** щоб додати пісні",

    # -- UI: Тимчасові повідомлення --
    "added_tracks":          "Додано **{count}** треків до черги",
    "added_song":            "Додано **{title}** до черги",
    "nothing_to_remove":     "Нічого видаляти.",
    "select_to_remove":      "Оберіть пісню для видалення:",
    "song_unavailable":      "Пісня більше недоступна.",
    "song_not_in_queue":     "Пісня більше не в черзі.",
    "song_not_in_history":   "Пісня більше не в історії.",
    "removed_from_queue":    "Видалено **{title}** з черги.",
    "removed_from_history":  "Видалено **{title}** з історії.",
    "remove_upcoming_desc":  "Наступна - {dur}",
    "remove_played_desc":    "Відтворена - {dur}",
    "remove_nothing_label":  "Нічого видаляти",
    "remove_select_placeholder": "Оберіть пісню для видалення...",

    # -- Фільтри (вивід команд) --
    "bass_boost_set":        "Підсилення басу: **{level}**",
    "bass_level_off":        "вимкнено",
    "bass_level_light":      "легке",
    "bass_level_medium":     "середнє",
    "bass_level_heavy":      "важке",

    # -- Мітки випадаючого фільтру --
    "filter_bass_light":     "Бас: Легкий",
    "filter_bass_medium":    "Бас: Середній",
    "filter_bass_heavy":     "Бас: Важкий",
    "filter_nightcore":      "Nightcore",
    "filter_vaporwave":      "Vaporwave",
    "filter_bass_light_desc": "+5дБ низькі частоти",
    "filter_bass_med_desc":  "+10дБ низькі частоти",
    "filter_bass_heavy_desc": "+15дБ низькі частоти",
    "filter_nc_desc":        "1.25x швидкість, вищий тон",
    "filter_vw_desc":        "0.8x швидкість, нижчий тон",
    "filter_placeholder":    "Аудіо фільтри...",

    # -- Власник: Бан / Тайм-аут --
    "ban_usage":             "Використання: `//ban @користувач`",
    "ban_done":              "**{user}** заблоковано від використання бота.",
    "unban_usage":           "Використання: `//unban @користувач`",
    "unban_done":            "**{user}** розблоковано.",
    "unban_not_banned":      "**{user}** не заблокований.",
    "timeout_usage":         "Використання: `//timeout @користувач <тривалість>` (напр. 10m, 1h, 1d)",
    "timeout_invalid":       "Невірна тривалість. Використовуйте число + s/m/h/d (напр. `30m`, `2h`).",
    "timeout_done":          "**{user}** заблоковано на **{duration}**.",
    "untimeout_usage":       "Використання: `//untimeout @користувач`",
    "untimeout_done":        "Тайм-аут **{user}** знято.",
    "untimeout_not_timed_out": "**{user}** не має тайм-ауту.",
    "restarting":            "Перезапуск бота...",
    "shutting_down":         "Вимкнення...",
    "log_empty":             "Записів логу ще немає.",
    "log_sent_dm":           "Логи відправлено в ОП.",
    "log_dm_failed":         "Не вдалося надіслати ОП — перевірте налаштування приватності.",

    # =======================================================================
    # ДОПОМОГА — Огляд
    # =======================================================================
    "help_title":       "🎵 Музичний бот — Довідка",
    "help_description": (
        "Музичний бот з інтерактивним Spotify-плеєром, "
        "підтримкою YouTube, аудіо фільтрами та керуванням чергою.\n\n"
        "**Порада:** Використовуйте `//start` щоб відкрити плеєр без команд!\n"
        "Або `//help <тема>` для детальної інформації."
    ),
    "help_cat_playback":     "▶️ Відтворення",
    "help_cat_playback_val": (
        "`//start` — Відкрити інтерактивний плеєр (додавайте пісні кнопкою)\n"
        "`//play <пісня/url>` — Відтворити пісню, пошуковий запит або плейлист\n"
        "`//playtop <пісня/url>` — Додати пісню на **початок** черги\n"
        "`//search <запит>` — Пошук на YouTube\n"
        "`//pause` — Призупинити трек\n"
        "`//resume` — Відновити відтворення\n"
        "`//skip` — Перейти до наступної пісні\n"
        "`//replay` — Перезапустити поточний трек з початку\n"
        "`//stop` — Зупинити, очистити чергу та відключитися"
    ),
    "help_cat_queue":        "📝 Керування чергою",
    "help_cat_queue_val": (
        "Плеєр має **випадаючу чергу** з відтвореними, поточними та наступними піснями.\n"
        "Натисніть на будь-яку пісню щоб перейти до неї.\n\n"
        "`//queue` або `//q` — Показати чергу (поточна + наступні 10)\n"
        "`//shuffle` — Перемішати порядок пісень у черзі\n"
        "`//clear` — Видалити всі пісні з черги\n"
        "`//remove <позиція>` — Видалити конкретну пісню (напр. `//remove 3`)\n"
        "`//skipto <позиція>` — Перейти до позиції\n"
        "`//swap <поз1> <поз2>` — Поміняти місцями дві пісні"
    ),
    "help_cat_settings":     "🎛️ Налаштування",
    "help_cat_settings_val": (
        "Всі налаштування доступні як **кнопки та меню** в плеєрі.\n\n"
        "`//volume <0-200>` — Встановити гучність (100 = норма, 200 = 2x)\n"
        "`//loop` — Переключити: вимк → один → черга → випадковий\n"
        "`//move` — Перемістити бота до вашого голосового каналу"
    ),
    "help_cat_filters":      "🎚️ Аудіо фільтри",
    "help_cat_filters_val": (
        "Оберіть фільтри у **випадаючому меню плеєра** — вони застосовуються миттєво!\n\n"
        "`//bass` — Підсилення басу (+10дБ низькі частоти)\n"
        "`//nightcore` — Найткор (на 25% швидше, вищий тон)\n"
        "`//vaporwave` — Вейпорвейв (на 20% повільніше, нижчий тон)\n"
        "*Найткор і вейпорвейв взаємовиключні; бас поєднується з обома.*"
    ),
    "help_cat_utility":      "🔧 Утиліти & AI",
    "help_cat_utility_val": (
        "`//dj <настрій/виконавець/жанр>` — AI підбирає 5 пісень під ваш вайб\n"
        "`//vibe` — AI аналізує настрій вашої черги та пропонує ще\n"
        "`//history` — Історія прослуховування, повтор пісень, AI смаковий профіль\n"
        "`//ask <будь-що>` — Запитати AI або сказати керувати ботом (з контекстом)\n"
        "`//personality <текст>` — Змінити персональність AI для цього сервера\n"
        "`//ping` — Перевірити затримку з'єднання бота\n"
        "`//lang <en|ua|ru>` — Змінити мову бота для цього сервера\n"
        "`//help` — Показати цей огляд"
    ),
    "help_cat_tips":         "💡 Корисно знати",
    "help_cat_tips_val": (
        "• **Інтерактивний плеєр:** `//start` — додавайте пісні, перемикайте, фільтруйте кнопками\n"
        "• **Ліміт черги:** максимум 100 пісень\n"
        "• **Авто-відключення:** 5 хв без активності або 1 хв на самоті\n"
        "• **Голосовий канал:** Ви повинні бути в каналі бота для керування\n"
        "• **Кулдаун:** 2 секунди між командами\n"
        "• **Джерела:** YouTube посилання, плейлисти та пошукові запити"
    ),
    "help_footer": "//help <тема> для деталей",

    # =======================================================================
    # ДОПОМОГА — Детальні сторінки
    # =======================================================================
    "help_play_title": "▶️ //play — Відтворити музику",
    "help_play_body": (
        "**Використання:** `//play <назва пісні або YouTube URL>`\n\n"
        "**Приклади:**\n"
        "• `//play never gonna give you up` — Пошук і відтворення\n"
        "• `//play https://youtube.com/watch?v=...` — Конкретне відео\n"
        "• `//play https://youtube.com/playlist?list=...` — Весь плейлист\n\n"
        "**Як це працює:**\n"
        "1. Якщо ви не в голосовому каналі, бот попросить приєднатися\n"
        "2. Якщо бот не підключений, він приєднується до вашого каналу\n"
        "3. Пісня додається в кінець черги\n"
        "4. Якщо нічого не грає, відтворення починається одразу\n\n"
        "**Див. також:** `//playtop` (додати на початок) · `//search` (результати пошуку)"
    ),
    "help_playtop_title": "⏫ //playtop — Відтворити наступною",
    "help_playtop_body": (
        "**Використання:** `//playtop <назва або URL>`\n\n"
        "Працює як `//play`, але додає пісню на **позицію #1** у черзі, "
        "тому вона відтвориться наступною.\n\n"
        "**Примітка:** Працює тільки з окремими піснями, не з плейлистами."
    ),
    "help_search_title": "🔍 //search — Пошук на YouTube",
    "help_search_body": (
        "**Використання:** `//search <запит>`\n\n"
        "**Приклад:** `//search lofi hip hop radio`\n\n"
        "Повертає 5 найкращих результатів з YouTube з назвою, каналом та тривалістю. "
        "Скопіюйте команду `//play` під кожним результатом, щоб додати в чергу."
    ),
    "help_pause_title": "⏸️ //pause та //resume",
    "help_pause_body": (
        "**`//pause`** — Призупинити поточний трек.\n"
        "**`//resume`** — Відновити призупинений трек.\n\n"
        "Ви повинні бути в голосовому каналі бота."
    ),
    "help_skip_title": "⏭️ //skip — Пропустити трек",
    "help_skip_body": (
        "**Використання:** `//skip`\n\n"
        "Пропускає поточну пісню та відтворює наступну з черги.\n"
        "Якщо увімкнено повтор одного треку, `//skip` тимчасово його вимкне.\n\n"
        "**Див. також:** `//skipto` (перейти до позиції) · `//replay` (перезапустити)"
    ),
    "help_skipto_title": "⏭️ //skipto — Перейти в черзі",
    "help_skipto_body": (
        "**Використання:** `//skipto <позиція>`\n\n"
        "**Приклад:** `//skipto 5` — Пропускає пісні 1-4 і відтворює пісню #5\n\n"
        "Всі пісні перед цільовою позицією видаляються з черги."
    ),
    "help_replay_title": "🔄 //replay — Перезапустити трек",
    "help_replay_body": (
        "**Використання:** `//replay`\n\n"
        "Перезапускає поточну пісню з початку. "
        "Працює незалежно від режиму повтору."
    ),
    "help_stop_title": "⏹️ //stop — Зупинити все",
    "help_stop_body": (
        "**Використання:** `//stop`\n\n"
        "Зупиняє відтворення, очищує чергу, скидає режим повтору "
        "та відключає бота від голосового каналу."
    ),
    "help_queue_title": "📜 //queue — Переглянути чергу",
    "help_queue_body": (
        "**Використання:** `//queue` або `//q`\n\n"
        "Показує поточну пісню та наступні 10 пісень у черзі, "
        "а також гучність та статус повтору.\n\n"
        "**Див. також:** `//np` (детальна інформація про поточний трек)"
    ),
    "help_np_title": "🎵 //nowplaying — Поточний трек",
    "help_np_body": (
        "**Використання:** `//np` або `//nowplaying`\n\n"
        "Показує детальну інформацію про поточний трек: назву, канал, "
        "тривалість, кількість переглядів, обкладинку, розмір черги, гучність та режим повтору."
    ),
    "help_shuffle_title": "🔀 //shuffle — Перемішати чергу",
    "help_shuffle_body": (
        "**Використання:** `//shuffle`\n\n"
        "Випадково змінює порядок пісень у черзі. "
        "Поточна пісня не змінюється.\n"
        "Потрібно щонайменше 2 пісні в черзі."
    ),
    "help_clear_title": "🗑️ //clear — Очистити чергу",
    "help_clear_body": (
        "**Використання:** `//clear`\n\n"
        "Видаляє всі пісні з черги. Поточна пісня продовжує грати "
        "(використовуйте `//stop` щоб також зупинити відтворення)."
    ),
    "help_remove_title": "❌ //remove — Видалити пісню",
    "help_remove_body": (
        "**Використання:** `//remove <позиція>`\n\n"
        "**Приклад:** `//remove 3` — Видаляє 3-тю пісню з черги\n\n"
        "Спочатку використовуйте `//queue` щоб побачити позиції."
    ),
    "help_swap_title": "🔄 //swap — Поміняти місцями",
    "help_swap_body": (
        "**Використання:** `//swap <поз1> <поз2>`\n\n"
        "**Приклад:** `//swap 1 5` — Міняє місцями 1-шу та 5-ту пісні\n\n"
        "Спочатку використовуйте `//queue` щоб побачити позиції."
    ),
    "help_volume_title": "🔊 //volume — Керування гучністю",
    "help_volume_body": (
        "**Використання:**\n"
        "• `//volume` — Показати поточну гучність\n"
        "• `//volume 50` — Встановити 50%\n"
        "• `//volume 150` — Встановити 150% (підсилено)\n\n"
        "**Діапазон:** 0 (без звуку) до 200 (2x підсилення).\n"
        "За замовчуванням 50%. Зміни застосовуються одразу."
    ),
    "help_loop_title": "🔁 //loop — Режими повтору",
    "help_loop_body": (
        "**Використання:**\n"
        "• `//loop` — Переключити: вимк → один → черга\n"
        "• `//loop off` — Вимкнути повтор\n"
        "• `//loop single` — Повторювати поточний трек нескінченно\n"
        "• `//loop queue` — Коли черга закінчиться, почати спочатку\n\n"
        "**Аліаси:** `off`/`none`/`no`, `single`/`one`/`song`, `queue`/`all`\n\n"
        "**Примітка:** `//skip` тимчасово відключає повтор одного треку."
    ),
    "help_move_title": "🔀 //move — Перемістити бота",
    "help_move_body": (
        "**Використання:** `//move`\n\n"
        "Переміщує бота до вашого голосового каналу. Корисно коли ви "
        "змінюєте канал без зупинки відтворення."
    ),
    "help_filters_title": "🎚️ Аудіо фільтри",
    "help_filters_body": (
        "**Команди:**\n"
        "• `//filters` — Показати активні фільтри\n"
        "• `//bass` — Підсилення басу (+10дБ низькі частоти)\n"
        "• `//nightcore` — Найткор (1.25x швидкість, вищий тон)\n"
        "• `//vaporwave` — Вейпорвейв (0.8x швидкість, нижчий тон)\n\n"
        "**Важливо:**\n"
        "• Фільтри застосовуються до **наступного** треку\n"
        "• Найткор і вейпорвейв взаємовиключні\n"
        "• Бас поєднується з найткором або вейпорвейвом\n"
        "• Усі фільтри включають нормалізацію звуку"
    ),
    "help_ping_title": "🏓 //ping — Перевірка затримки",
    "help_ping_body": (
        "**Використання:** `//ping`\n\n"
        "Показує затримку шлюзу бота (з'єднання з Discord) та "
        "затримку голосу (якщо підключений до голосового каналу)."
    ),
    "help_lang_title": "🌐 //lang — Мова",
    "help_lang_body": (
        "**Використання:** `//lang <en|ua|ru>`\n\n"
        "Змінює мову бота для цього сервера.\n"
        "• `en` — English (Англійська)\n"
        "• `ua` — Українська\n"
        "• `ru` — Кацапський (Російська)\n\n"
        "Налаштування мови зберігається для кожного сервера."
    ),
    "help_ask_title": "🤖 //ask — AI Асистент & Оператор",
    "help_ask_body": (
        "**Використання:** `//ask <питання або команда>`\n\n"
        "**Приклади:**\n"
        "• `//ask Який жанр цієї пісні?` — питання про те, що грає\n"
        "• `//ask грай щось чілл` — AI додає 5 чілл пісень\n"
        "• `//ask скіп і гучніше` — керує ботом\n"
        "• `//ask додай 5 пісень як Deftones` — AI підбирає пісні\n"
        "• `//ask який вайб цієї черги?` — аналізує настрій\n\n"
        "AI знає що грає, чергу, гучність, фільтри та історію.\n"
        "Коли ви в голосовому каналі, він також може керувати ботом.\n"
        "Денний ліміт на користувача."
    ),
    "help_personality_title": "🎭 //personality — Персональність AI",
    "help_personality_body": (
        "**Використання:**\n"
        "• `//personality` — Показати поточну персональність AI\n"
        "• `//personality <текст>` — Встановити персональність для цього сервера\n"
        "• `//personality reset` — Скинути до стандартної\n\n"
        "**Приклад:** `//personality Ти саркастичний пірат, який говорить тільки про морські пісні`\n\n"
        "Персональність впливає на відповіді AI через `//ask`.\n"
        "Максимум 500 символів. Зберігається для кожного сервера."
    ),
    "help_dj_title": "🎧 //dj — AI DJ",
    "help_dj_body": (
        "**Використання:** `//dj <настрій, виконавець або жанр>`\n\n"
        "**Приклади:**\n"
        "• `//dj чілл вайб для навчання`\n"
        "• `//dj як Deftones`\n"
        "• `//dj 90-ті хіп-хоп класика`\n"
        "• `//dj енергійна електроніка для тренування`\n\n"
        "AI підбирає 5 пісень під ваш опис та додає їх у чергу.\n"
        "Працює з настроями, виконавцями, жанрами, епохами або будь-якою комбінацією.\n"
        "Використовує один денний AI кредит."
    ),
    "help_vibe_title": "🎵 //vibe — Аналіз вайбу",
    "help_vibe_body": (
        "**Використання:** `//vibe`\n\n"
        "AI аналізує поточний трек та чергу, описує загальний настрій\n"
        "та пропонує пісні, які б підійшли.\n\n"
        "Враховує поточний трек, історію та наступні пісні у черзі.\n"
        "Використовує один денний AI кредит."
    ),
    "help_history_title": "📜 //history — Історія прослуховування",
    "help_history_body": (
        "**Використання:** `//history`\n\n"
        "Показує всі пісні, зіграні на цьому сервері, згруповані за користувачами.\n"
        "Включає випадаючий список для повтору будь-якої пісні з історії.\n\n"
        "**AI Смаковий профіль** (з'являється при 5+ піснях):\n"
        "Claude аналізує смаки кожного та описує музичні вподобання.\n"
        "Використовує один денний AI кредит."
    ),
    "help_unknown_topic": "❓ Невідома тема",
    "help_unknown_body":  "Допомога для `{topic}` не знайдена.\n\n**Доступні теми:**\n{topics}",
    "help_topic_footer":  "//help для повного списку команд",
}


# --------------------------------------------------------------------------
# RUSSIAN
# --------------------------------------------------------------------------

S["ru"] = {
    # -- Общие --
    "need_voice":        "❌ Вы должны быть в голосовом канале!",
    "need_bot_channel":  "❌ Вы должны быть в голосовом канале бота!",
    "session_expired":   "⚠️ Сессия плеера истекла. Используйте `//play` чтобы начать новую, или ➕ чтобы добавить песню.",
    "need_same_channel": "❌ Вы должны быть в том же голосовом канале, что и бот!",

    # -- Воспроизведение --
    "provide_song":    "❌ Пожалуйста, укажите название песни или URL.",
    "searching":       "🔍 Ищу...",
    "song_not_found":  "❌ Не удалось найти эту песню. Попробуйте другой запрос.",
    "nothing_playing": "❌ Ничего не воспроизводится",
    "nothing_paused":  "❌ Ничего не приостановлено",
    "not_connected":   "❌ Бот не подключён к голосовому каналу",
    "paused":          "⏸️ Приостановлено",
    "resumed":         "▶️ Возобновлено",
    "skipped":         "⏭️ Пропущено",
    "stopped":         "⏹️ Остановлено и отключено",

    # -- Очередь --
    "queue_full":          "❌ Очередь заполнена (максимум {max} треков).",
    "queue_empty":         "📭 Очередь пуста",
    "queue_already_empty": "❌ Очередь уже пуста",
    "playlist_added":      "📝 Плейлист добавлен",
    "playlist_added_desc": "Добавлено **{count}** треков в очередь",
    "added_to_queue":      "Добавлено в очередь",
    "added_to_top":        "Добавлено в начало очереди",
    "now_playing":         "Сейчас играет",
    "up_next":             "Далее",
    "songs_in_queue":      "{count} песен в очереди",
    "up_next_count":       "Далее ({count} песен)",
    "music_queue":         "📜 Музыкальная очередь",
    "and_more":            "*...и ещё {count}*",
    "position":            "Позиция",
    "next_up":             "#1 (следующая)",

    # -- Поля эмбеда --
    "channel_field": "Канал",
    "duration_field": "Длительность",
    "views_field":    "Просмотры",
    "queue_field":    "Очередь",
    "volume_field":   "Громкость",
    "loop_field":     "Повтор",
    "powered_by":     "Работает на yt-dlp",

    # -- Громкость --
    "volume_current": "🔊 Громкость: **{vol}%**",
    "volume_set":     "🔊 Громкость установлена на **{vol}%**",
    "volume_range":   "❌ Громкость должна быть от 0 до 200",
    "invalid_volume": "❌ Неверное значение громкости",

    # -- Повтор --
    "loop_off":      "➡️ Повтор: **Выключен**",
    "loop_single":   "🔂 Повтор: **Один трек**",
    "loop_queue":    "🔁 Повтор: **Вся очередь**",
    "loop_shuffle":  "🔀 Повтор: **Случайный**",
    "invalid_loop":  "❌ Неверный режим повтора. Используйте: `off`, `single` или `queue`",

    # -- Перемешать / Очистить / Удалить --
    "shuffled":          "🔀 Перемешано {count} песен",
    "need_2_songs":      "❌ Нужно минимум 2 песни в очереди для перемешивания",
    "cleared":           "🗑️ Удалено {count} песен из очереди",
    "removed":           "✅ Удалено: **{title}**",
    "invalid_position":  "❌ Неверная позиция",
    "invalid_number":    "❌ Неверный номер позиции",

    # -- Переход --
    "skipto_usage":   "❌ Использование: `//skipto <позиция>` (напр. `//skipto 3`)",
    "skipto_invalid": "❌ Неверная позиция. В очереди {count} песен.",
    "skipto_msg":     "⏭️ Пропущено {count} песен, переход к **{title}**",

    # -- Повтор трека --
    "replay_msg":        "🔄 Повторяю текущий трек",
    "nothing_to_replay": "❌ Нечего повторять",

    # -- Playtop --
    "playtop_usage":       "❌ Использование: `//playtop <песня/url>`",
    "playtop_no_playlist": "❌ `//playtop` работает только с отдельными песнями, не с плейлистами. Используйте `//play`.",

    # -- Обмен --
    "swap_usage":    "❌ Использование: `//swap <поз1> <поз2>` (напр. `//swap 1 3`)",
    "swap_range":    "❌ Позиции должны быть от 1 до {count}",
    "swap_same":     "❌ Позиции должны быть разными",
    "swapped":       "🔄 Поменяно **{a}** (#{a_pos}) с **{b}** (#{b_pos})",

    # -- Перемещение --
    "moved":              "🔀 Перемещён в **{channel}**",
    "already_in_channel": "❌ Бот уже в вашем канале!",
    "bot_not_in_voice":   "❌ Бот не подключён к голосовому каналу",

    # -- Пинг --
    "ping_msg":       "🏓 Понг! Задержка шлюза: **{gateway}мс**",
    "voice_latency":  "\nЗадержка голоса: **{voice}мс**",

    # -- Поиск --
    "search_usage":   "❌ Использование: //search <запрос>",
    "search_results": "🔍 Результаты поиска: {query}",
    "no_results":     "❌ Ничего не найдено",

    # -- Фильтры --
    "audio_filters":  "🎛️ Аудио фильтры",
    "filters_cmds":   "Команды",
    "filters_desc":   "`//bass` — Усиление басов\n`//nightcore` — Найткор\n`//vaporwave` — Вейпорвейв",
    "active":         "✅ Активен",
    "inactive":       "❌ Неактивен",
    "bass_on":        "🔊 Усиление басов **включено**",
    "bass_off":       "🔊 Усиление басов **выключено**",
    "nightcore_on":   "⚡ Найткор **включён**",
    "nightcore_off":  "⚡ Найткор **выключен**",
    "vaporwave_on":   "🌊 Вейпорвейв **включён**",
    "vaporwave_off":  "🌊 Вейпорвейв **выключен**",
    "speed":          "Скорость",
    "progress":       "Прогресс",
    "filters_active": "Фильтры",
    "filters_restart_note": "Изменения применяются сразу с текущей позиции.",
    "filters_next_note":    "Фильтры применятся когда начнётся трек.",
    "nightcore_vaporwave_exclusive": "Найткор и Вейпорвейв нельзя использовать одновременно.",

    # -- Ошибки --
    "error":              "❌ Ошибка",
    "connection_failed":  "❌ Не удалось подключиться",
    "playback_error":     "❌ Ошибка воспроизведения",
    "playback_error_desc": "Не удалось воспроизвести: **{title}**\nПереход к следующему треку...",
    "search_error":       "❌ Ошибка поиска",

    # -- Язык --
    "lang_set":     "🌐 Язык изменён на **{lang}**",
    "lang_current": "🌐 Текущий язык: **{lang}**\nИспользуйте `//lang <en|ua|ru>` для смены.",
    "lang_invalid": "❌ Неверный язык. Доступные: `en` 🇬🇧 English, `ua` 🇺🇦 Українська, `ru` 🦅🦅 Кацапський",

    # -- Remove usage --
    "remove_usage": "❌ Использование: `//remove <позиция>`",

    # -- AI Ассистент --
    "ask_usage":          "❌ Использование: `//ask <вопрос>`",
    "ask_thinking":       "🤔 Думаю...",
    "ask_error":          "❌ Не удалось получить ответ. Попробуйте ещё раз.",
    "ask_not_configured": "❌ AI ассистент не настроен.",
    "ask_limit_hit":      "❌ Дневной лимит исчерпан ({used}/{max}). Сброс в полночь UTC.",
    "ask_remaining":      "💬 AI ответ ({used}/{max} дневных запросов)",

    # -- Персональность --
    "personality_current":  "🎭 Текущая персональность:\n> {text}\n\nИспользуйте `//personality <текст>` для смены или `//personality reset` для стандартной.",
    "personality_set":      "🎭 Персональность обновлена:\n> {text}",
    "personality_reset":    "🎭 Персональность сброшена на стандартную.",
    "personality_too_long": "❌ Текст персональности слишком длинный (максимум 500 символов).",

    # -- AI DJ --
    "dj_usage":      "❌ Использование: `//dj <настроение, исполнитель или жанр>`\nПримеры: `//dj чилл вайб` · `//dj как Deftones` · `//dj 90-е хип-хоп`",
    "dj_thinking":   "🎧 AI DJ подбирает песни...",
    "dj_error":      "❌ AI DJ не смог создать плейлист. Попробуйте ещё раз.",
    "dj_added":      "🎧 AI DJ добавил {count} песен",
    "dj_no_results": "❌ Не удалось найти ни одну из предложенных песен на YouTube.",

    # -- Vibe Check --
    "vibe_thinking":        "🎵 Анализирую вайб...",
    "vibe_nothing_playing": "❌ Ничего не играет. Сначала добавьте песни!",

    # -- История прослушивания --
    "history_empty":            "📭 История прослушивания пуста. Сначала послушайте песни!",
    "history_title":            "📜 История прослушивания",
    "history_total":            "песен всего",
    "history_play_placeholder": "🔁 Переиграть песню из истории...",
    "history_profile_btn":      "🧠 AI Вкусовой профиль",
    # -- UI: Кнопки плеера --
    "btn_prev":          "Назад",
    "btn_rewind":        "-15с",
    "btn_pause":         "Пауза",
    "btn_resume":        "Далее",
    "btn_forward":       "+15с",
    "btn_skip":          "Далее",
    "btn_add":           "Добав.",
    "btn_loop_off":      "Повтор: Нет",
    "btn_loop_single":   "Повтор: Один",
    "btn_loop_queue":    "Повтор: Все",
    "btn_loop_shuffle":  "Случай.",
    "btn_remove":        "Удалить",
    "btn_clear":         "Очист.",
    "btn_stop":          "Стоп",
    "btn_add_song":      "Добавить песню",
    "btn_disconnect":    "Отключить",
    "bass_off_label":    "Бас: Нет",
    "bass_light_label":  "Бас: Лёгкий",
    "bass_med_label":    "Бас: Сред.",
    "bass_heavy_label":  "Бас: Тяж.",
    "btn_nightcore":     "Найткор",
    "btn_vaporwave":     "Вейпорвейв",

    # -- UI: Выпадающие меню --
    "vol_placeholder":       "Громкость: {vol}%",
    "queue_placeholder":     "Очередь: {played} проиграно, {upcoming} далее",
    "queue_placeholder_short": "Очередь: {upcoming} далее",
    "queue_now_playing":     "Сейчас играет",
    "queue_played":          "Проиграно",
    "queue_upcoming":        "Далее",
    "remove_placeholder":    "Выберите песню для удаления...",

    # -- UI: Модальное окно --
    "modal_add_song":        "Добавить песню",
    "modal_song_label":      "Название песни или URL",
    "modal_song_placeholder": "напр. Nirvana - Smells Like Teen Spirit",

    # -- UI: Плеер --
    "player_title":          "Музыкальный плеер",
    "player_idle_desc":      "Нажмите **+ Добав.** чтобы добавить песни",

    # -- UI: Временные сообщения --
    "added_tracks":          "Добавлено **{count}** треков в очередь",
    "added_song":            "Добавлено **{title}** в очередь",
    "nothing_to_remove":     "Нечего удалять.",
    "select_to_remove":      "Выберите песню для удаления:",
    "song_unavailable":      "Песня больше недоступна.",
    "song_not_in_queue":     "Песня больше не в очереди.",
    "song_not_in_history":   "Песня больше не в истории.",
    "removed_from_queue":    "Удалено **{title}** из очереди.",
    "removed_from_history":  "Удалено **{title}** из истории.",
    "remove_upcoming_desc":  "Следующая - {dur}",
    "remove_played_desc":    "Прослушана - {dur}",
    "remove_nothing_label":  "Нечего удалять",
    "remove_select_placeholder": "Выберите песню для удаления...",

    # -- Фильтры (вывод команд) --
    "bass_boost_set":        "Усиление басов: **{level}**",
    "bass_level_off":        "выключено",
    "bass_level_light":      "лёгкое",
    "bass_level_medium":     "среднее",
    "bass_level_heavy":      "тяжёлое",

    # -- Метки выпадающего фильтра --
    "filter_bass_light":     "Бас: Лёгкий",
    "filter_bass_medium":    "Бас: Средний",
    "filter_bass_heavy":     "Бас: Тяжёлый",
    "filter_nightcore":      "Nightcore",
    "filter_vaporwave":      "Vaporwave",
    "filter_bass_light_desc": "+5дБ низкие частоты",
    "filter_bass_med_desc":  "+10дБ низкие частоты",
    "filter_bass_heavy_desc": "+15дБ низкие частоты",
    "filter_nc_desc":        "1.25x скорость, выше тон",
    "filter_vw_desc":        "0.8x скорость, ниже тон",
    "filter_placeholder":    "Аудио фильтры...",

    # -- Владелец: Бан / Тайм-аут --
    "ban_usage":             "Использование: `//ban @пользователь`",
    "ban_done":              "**{user}** заблокирован.",
    "unban_usage":           "Использование: `//unban @пользователь`",
    "unban_done":            "**{user}** разблокирован.",
    "unban_not_banned":      "**{user}** не заблокирован.",
    "timeout_usage":         "Использование: `//timeout @пользователь <время>` (напр. 10m, 1h, 1d)",
    "timeout_invalid":       "Неверное время. Используйте число + s/m/h/d (напр. `30m`, `2h`).",
    "timeout_done":          "**{user}** заблокирован на **{duration}**.",
    "untimeout_usage":       "Использование: `//untimeout @пользователь`",
    "untimeout_done":        "Тайм-аут **{user}** снят.",
    "untimeout_not_timed_out": "**{user}** не в тайм-ауте.",
    "restarting":            "Перезапуск бота...",
    "shutting_down":         "Выключение...",
    "log_empty":             "Записей лога пока нет.",
    "log_sent_dm":           "Логи отправлены в ЛС.",
    "log_dm_failed":         "Не удалось отправить ЛС — проверьте настройки приватности.",

    # =======================================================================
    # ПОМОЩЬ — Обзор
    # =======================================================================
    "help_title":       "🎵 Музыкальный бот — Справочник команд",
    "help_description": (
        "Музыкальный бот с интерактивным Spotify-плеером, "
        "поддержкой YouTube, аудио фильтрами и управлением очередью.\n\n"
        "**Совет:** Используйте `//start` чтобы открыть плеер без команд!\n"
        "Или `//help <тема>` для подробной информации."
    ),
    "help_cat_playback":     "▶️ Воспроизведение",
    "help_cat_playback_val": (
        "`//start` — Открыть интерактивный плеер (добавляйте песни кнопкой)\n"
        "`//play <песня/url>` — Воспроизвести песню, поисковый запрос или плейлист\n"
        "`//playtop <песня/url>` — Добавить песню в **начало** очереди\n"
        "`//search <запрос>` — Поиск на YouTube\n"
        "`//pause` — Приостановить трек\n"
        "`//resume` — Возобновить воспроизведение\n"
        "`//skip` — Перейти к следующей песне\n"
        "`//replay` — Перезапустить текущий трек с начала\n"
        "`//stop` — Остановить, очистить очередь и отключиться"
    ),
    "help_cat_queue":        "📝 Управление очередью",
    "help_cat_queue_val": (
        "В плеере есть **выпадающая очередь** с проигранными, текущей и следующими песнями.\n"
        "Нажмите на любую песню чтобы перейти к ней.\n\n"
        "`//queue` или `//q` — Показать очередь (текущая + следующие 10)\n"
        "`//shuffle` — Перемешать порядок песен в очереди\n"
        "`//clear` — Удалить все песни из очереди\n"
        "`//remove <позиция>` — Удалить конкретную песню (напр. `//remove 3`)\n"
        "`//skipto <позиция>` — Перейти к позиции\n"
        "`//swap <поз1> <поз2>` — Поменять местами две песни"
    ),
    "help_cat_settings":     "🎛️ Настройки",
    "help_cat_settings_val": (
        "Все настройки доступны как **кнопки и меню** в плеере.\n\n"
        "`//volume <0-200>` — Установить громкость (100 = норма, 200 = 2x)\n"
        "`//loop` — Переключить: выкл → один → очередь → случайный\n"
        "`//move` — Переместить бота в ваш голосовой канал"
    ),
    "help_cat_filters":      "🎚️ Аудио фильтры",
    "help_cat_filters_val": (
        "Выберите фильтры в **выпадающем меню плеера** — они применяются мгновенно!\n\n"
        "`//bass` — Усиление басов (+10дБ низкие частоты)\n"
        "`//nightcore` — Найткор (на 25% быстрее, выше тон)\n"
        "`//vaporwave` — Вейпорвейв (на 20% медленнее, ниже тон)\n"
        "*Найткор и вейпорвейв взаимоисключающие; басы сочетаются с обоими.*"
    ),
    "help_cat_utility":      "🔧 Утилиты & AI",
    "help_cat_utility_val": (
        "`//dj <настроение/исполнитель/жанр>` — AI подбирает 5 песен под ваш вайб\n"
        "`//vibe` — AI анализирует настроение вашей очереди и предлагает ещё\n"
        "`//history` — История прослушивания, повтор песен, AI вкусовой профиль\n"
        "`//ask <что угодно>` — Спросить AI или сказать управлять ботом (с контекстом)\n"
        "`//personality <текст>` — Настроить персональность AI для этого сервера\n"
        "`//ping` — Проверить задержку соединения бота\n"
        "`//lang <en|ua|ru>` — Изменить язык бота для этого сервера\n"
        "`//help` — Показать этот обзор"
    ),
    "help_cat_tips":         "💡 Полезно знать",
    "help_cat_tips_val": (
        "• **Интерактивный плеер:** `//start` — добавляйте песни, переключайте, фильтруйте кнопками\n"
        "• **Лимит очереди:** максимум 100 песен\n"
        "• **Авто-отключение:** 5 мин без активности или 1 мин в одиночестве\n"
        "• **Голосовой канал:** Вы должны быть в канале бота для управления\n"
        "• **Кулдаун:** 2 секунды между командами\n"
        "• **Источники:** YouTube ссылки, плейлисты и поисковые запросы"
    ),
    "help_footer": "//help <тема> для подробностей",

    # =======================================================================
    # ПОМОЩЬ — Детальные страницы
    # =======================================================================
    "help_play_title": "▶️ //play — Воспроизвести музыку",
    "help_play_body": (
        "**Использование:** `//play <название песни или YouTube URL>`\n\n"
        "**Примеры:**\n"
        "• `//play never gonna give you up` — Поиск и воспроизведение\n"
        "• `//play https://youtube.com/watch?v=...` — Конкретное видео\n"
        "• `//play https://youtube.com/playlist?list=...` — Весь плейлист\n\n"
        "**Как это работает:**\n"
        "1. Если вы не в голосовом канале, бот попросит присоединиться\n"
        "2. Если бот не подключён, он присоединяется к вашему каналу\n"
        "3. Песня добавляется в конец очереди\n"
        "4. Если ничего не играет, воспроизведение начинается сразу\n\n"
        "**См. также:** `//playtop` (добавить в начало) · `//search` (результаты поиска)"
    ),
    "help_playtop_title": "⏫ //playtop — Воспроизвести следующей",
    "help_playtop_body": (
        "**Использование:** `//playtop <название или URL>`\n\n"
        "Работает как `//play`, но добавляет песню на **позицию #1** в очереди, "
        "поэтому она воспроизведётся следующей.\n\n"
        "**Примечание:** Работает только с отдельными песнями, не с плейлистами."
    ),
    "help_search_title": "🔍 //search — Поиск на YouTube",
    "help_search_body": (
        "**Использование:** `//search <запрос>`\n\n"
        "**Пример:** `//search lofi hip hop radio`\n\n"
        "Возвращает 5 лучших результатов с YouTube с названием, каналом и длительностью. "
        "Скопируйте команду `//play` под каждым результатом, чтобы добавить в очередь."
    ),
    "help_pause_title": "⏸️ //pause и //resume",
    "help_pause_body": (
        "**`//pause`** — Приостановить текущий трек.\n"
        "**`//resume`** — Возобновить приостановленный трек.\n\n"
        "Вы должны быть в голосовом канале бота."
    ),
    "help_skip_title": "⏭️ //skip — Пропустить трек",
    "help_skip_body": (
        "**Использование:** `//skip`\n\n"
        "Пропускает текущую песню и воспроизводит следующую из очереди.\n"
        "Если включён повтор одного трека, `//skip` временно его отключит.\n\n"
        "**См. также:** `//skipto` (перейти к позиции) · `//replay` (перезапустить)"
    ),
    "help_skipto_title": "⏭️ //skipto — Перейти в очереди",
    "help_skipto_body": (
        "**Использование:** `//skipto <позиция>`\n\n"
        "**Пример:** `//skipto 5` — Пропускает песни 1-4 и воспроизводит песню #5\n\n"
        "Все песни перед целевой позицией удаляются из очереди."
    ),
    "help_replay_title": "🔄 //replay — Перезапустить трек",
    "help_replay_body": (
        "**Использование:** `//replay`\n\n"
        "Перезапускает текущую песню с начала. "
        "Работает независимо от режима повтора."
    ),
    "help_stop_title": "⏹️ //stop — Остановить всё",
    "help_stop_body": (
        "**Использование:** `//stop`\n\n"
        "Останавливает воспроизведение, очищает очередь, сбрасывает режим повтора "
        "и отключает бота от голосового канала."
    ),
    "help_queue_title": "📜 //queue — Просмотр очереди",
    "help_queue_body": (
        "**Использование:** `//queue` или `//q`\n\n"
        "Показывает текущую песню и следующие 10 песен в очереди, "
        "а также громкость и статус повтора.\n\n"
        "**См. также:** `//np` (подробная информация о текущем треке)"
    ),
    "help_np_title": "🎵 //nowplaying — Текущий трек",
    "help_np_body": (
        "**Использование:** `//np` или `//nowplaying`\n\n"
        "Показывает подробную информацию о текущем треке: название, канал, "
        "длительность, количество просмотров, обложку, размер очереди, громкость и режим повтора."
    ),
    "help_shuffle_title": "🔀 //shuffle — Перемешать очередь",
    "help_shuffle_body": (
        "**Использование:** `//shuffle`\n\n"
        "Случайным образом меняет порядок песен в очереди. "
        "Текущая песня не затрагивается.\n"
        "Нужно минимум 2 песни в очереди."
    ),
    "help_clear_title": "🗑️ //clear — Очистить очередь",
    "help_clear_body": (
        "**Использование:** `//clear`\n\n"
        "Удаляет все песни из очереди. Текущая песня продолжает играть "
        "(используйте `//stop` чтобы также остановить воспроизведение)."
    ),
    "help_remove_title": "❌ //remove — Удалить песню",
    "help_remove_body": (
        "**Использование:** `//remove <позиция>`\n\n"
        "**Пример:** `//remove 3` — Удаляет 3-ю песню из очереди\n\n"
        "Сначала используйте `//queue` чтобы увидеть позиции."
    ),
    "help_swap_title": "🔄 //swap — Поменять местами",
    "help_swap_body": (
        "**Использование:** `//swap <поз1> <поз2>`\n\n"
        "**Пример:** `//swap 1 5` — Меняет местами 1-ю и 5-ю песни\n\n"
        "Сначала используйте `//queue` чтобы увидеть позиции."
    ),
    "help_volume_title": "🔊 //volume — Управление громкостью",
    "help_volume_body": (
        "**Использование:**\n"
        "• `//volume` — Показать текущую громкость\n"
        "• `//volume 50` — Установить 50%\n"
        "• `//volume 150` — Установить 150% (усиление)\n\n"
        "**Диапазон:** 0 (без звука) до 200 (2x усиление).\n"
        "По умолчанию 50%. Изменения применяются сразу."
    ),
    "help_loop_title": "🔁 //loop — Режимы повтора",
    "help_loop_body": (
        "**Использование:**\n"
        "• `//loop` — Переключить: выкл → один → очередь\n"
        "• `//loop off` — Выключить повтор\n"
        "• `//loop single` — Повторять текущий трек бесконечно\n"
        "• `//loop queue` — Когда очередь закончится, начать сначала\n\n"
        "**Алиасы:** `off`/`none`/`no`, `single`/`one`/`song`, `queue`/`all`\n\n"
        "**Примечание:** `//skip` временно отключает повтор одного трека."
    ),
    "help_move_title": "🔀 //move — Переместить бота",
    "help_move_body": (
        "**Использование:** `//move`\n\n"
        "Перемещает бота в ваш голосовой канал. Полезно когда вы "
        "меняете канал без остановки воспроизведения."
    ),
    "help_filters_title": "🎚️ Аудио фильтры",
    "help_filters_body": (
        "**Команды:**\n"
        "• `//filters` — Показать активные фильтры\n"
        "• `//bass` — Усиление басов (+10дБ низкие частоты)\n"
        "• `//nightcore` — Найткор (1.25x скорость, выше тон)\n"
        "• `//vaporwave` — Вейпорвейв (0.8x скорость, ниже тон)\n\n"
        "**Важно:**\n"
        "• Фильтры применяются к **следующему** треку\n"
        "• Найткор и вейпорвейв взаимоисключающие\n"
        "• Басы сочетаются с найткором или вейпорвейвом\n"
        "• Все фильтры включают нормализацию звука"
    ),
    "help_ping_title": "🏓 //ping — Проверка задержки",
    "help_ping_body": (
        "**Использование:** `//ping`\n\n"
        "Показывает задержку шлюза бота (соединение с Discord) и "
        "задержку голоса (если подключён к голосовому каналу)."
    ),
    "help_lang_title": "🌐 //lang — Язык",
    "help_lang_body": (
        "**Использование:** `//lang <en|ua|ru>`\n\n"
        "Изменяет язык бота для этого сервера.\n"
        "• `en` — English (Английский)\n"
        "• `ua` — Українська (Украинский)\n"
        "• `ru` — Кацапський\n\n"
        "Настройка языка сохраняется для каждого сервера."
    ),
    "help_ask_title": "🤖 //ask — AI Ассистент & Оператор",
    "help_ask_body": (
        "**Использование:** `//ask <вопрос или команда>`\n\n"
        "**Примеры:**\n"
        "• `//ask Какой жанр этой песни?` — вопрос о том, что играет\n"
        "• `//ask играй что-то чилл` — AI добавит 5 чилл песен\n"
        "• `//ask скип и погромче` — управляет ботом\n"
        "• `//ask добавь 5 песен как Deftones` — AI подберёт песни\n"
        "• `//ask какой вайб этой очереди?` — анализирует настроение\n\n"
        "AI знает что играет, очередь, громкость, фильтры и историю.\n"
        "Когда вы в голосовом канале, он также может управлять ботом.\n"
        "Дневной лимит на пользователя."
    ),
    "help_personality_title": "🎭 //personality — Персональность AI",
    "help_personality_body": (
        "**Использование:**\n"
        "• `//personality` — Показать текущую персональность AI\n"
        "• `//personality <текст>` — Установить персональность для этого сервера\n"
        "• `//personality reset` — Сбросить на стандартную\n\n"
        "**Пример:** `//personality Ты саркастичный пират, который говорит только о морских песнях`\n\n"
        "Персональность влияет на ответы AI через `//ask`.\n"
        "Максимум 500 символов. Сохраняется для каждого сервера."
    ),
    "help_dj_title": "🎧 //dj — AI DJ",
    "help_dj_body": (
        "**Использование:** `//dj <настроение, исполнитель или жанр>`\n\n"
        "**Примеры:**\n"
        "• `//dj чилл вайб для учёбы`\n"
        "• `//dj как Deftones`\n"
        "• `//dj 90-е хип-хоп классика`\n"
        "• `//dj энергичная электроника для тренировки`\n\n"
        "AI подбирает 5 песен под ваше описание и добавляет их в очередь.\n"
        "Работает с настроениями, исполнителями, жанрами, эпохами или любой комбинацией.\n"
        "Использует один дневной AI кредит."
    ),
    "help_vibe_title": "🎵 //vibe — Анализ вайба",
    "help_vibe_body": (
        "**Использование:** `//vibe`\n\n"
        "AI анализирует текущий трек и очередь, описывает общее настроение\n"
        "и предлагает песни, которые бы подошли.\n\n"
        "Учитывает текущий трек, историю и следующие песни в очереди.\n"
        "Использует один дневной AI кредит."
    ),
    "help_history_title": "📜 //history — История прослушивания",
    "help_history_body": (
        "**Использование:** `//history`\n\n"
        "Показывает все песни, сыгранные на этом сервере, сгруппированные по пользователям.\n"
        "Включает выпадающий список для повтора любой песни из истории.\n\n"
        "**AI Вкусовой профиль** (появляется при 5+ песнях):\n"
        "Claude анализирует вкусы каждого и описывает музыкальные предпочтения.\n"
        "Использует один дневной AI кредит."
    ),
    "help_unknown_topic": "❓ Неизвестная тема",
    "help_unknown_body":  "Справка для `{topic}` не найдена.\n\n**Доступные темы:**\n{topics}",
    "help_topic_footer":  "//help для полного списка команд",
}
