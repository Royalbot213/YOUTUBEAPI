import os
import io
import asyncio
from datetime import datetime, timedelta

from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import database


# =========================================================
# HEROKU CONFIG VARS
# =========================================================

def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required Heroku Config Var: {name}")
    return value


API_ID = int(require_env("API_ID"))
API_HASH = require_env("API_HASH")
BOT_TOKEN = require_env("BOT_TOKEN")


# =========================================================
# PYROGRAM CLIENT
# =========================================================

# Pyrogram may access the current asyncio loop while creating the client.
# Heroku/Python 3.11 may start with no loop in MainThread, so create one first.
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

app = Client(
    "YouTubeapi",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# =========================================================
# MAIN MENU
# =========================================================

def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔑 View Your Key",
                callback_data="view_key"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Usage",
                callback_data="view_key"
            )
        ],
        [
            InlineKeyboardButton(
                "📚 API Docs",
                callback_data="api_docs"
            ),
            InlineKeyboardButton(
                "💬 Support ↗",
                url="https://t.me/ll_ROYAL_ABOUT_ll"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Channel ↗",
                url="https://t.me/ll_ROYAL_ABOUT_ll"
            )
        ]
    ])


# =========================================================
# /START
# =========================================================

@app.on_message(
    filters.command("start") &
    filters.private
)
async def start_cmd(client, message):

    user_id = message.from_user.id

    try:
        await database.get_or_create_key(user_id)

        text = (
            f"👋 **Welcome {message.from_user.mention}!**\n\n"
            "**Main Menu**"
        )

        await message.reply_text(
            text,
            reply_markup=get_main_menu_keyboard()
        )

    except Exception as e:

        print(f"START ERROR: {e}")

        await message.reply_text(
            "⚠️ Something went wrong while processing your request."
        )


# =========================================================
# API KEY PAGE
# =========================================================

async def render_key_page(query, user_id):

    api_key, expiry_date, _ = await database.get_or_create_key(
        user_id
    )

    now = datetime.now()

    days_left = max(
        (expiry_date - now).days,
        0
    )

    expiry_str = expiry_date.strftime(
        "%d %b %Y, %I:%M %p IST"
    )

    created_date = expiry_date - timedelta(
        days=30
    )

    created_str = created_date.strftime(
        "%d %b %Y, %I:%M %p IST"
    )

    text = (
        "🔑 **Your API Key**\n\n"

        "**API Key:**\n"
        f"`{api_key}`\n\n"

        "**Status:** 🟢 Active\n"
        "**Daily Limit:** 3,000\n\n"

        "**Today's Usage:**\n"
        "📊 Requests: 0\n"
        "🎵 Audio: 0\n"
        "🎬 Video: 0\n\n"

        "**All-Time Usage:**\n"
        "📊 Total Requests: 0\n"
        "🎵 Total Audio: 0\n"
        "🎬 Total Video: 0\n\n"

        f"**Created:** {created_str}\n"
        f"**Expires:** {expiry_str}\n"
        f"**Days Left:** {days_left} days"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Renew",
                callback_data="action_renew"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 Revoke & Get New Key",
                callback_data="action_revoke"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="main_menu"
            )
        ]
    ])

    await query.message.edit_text(
        text,
        reply_markup=keyboard
    )


# =========================================================
# CALLBACK QUERY
# =========================================================

@app.on_callback_query()
async def on_callback(client, query):

    user_id = query.from_user.id
    data = query.data

    try:

        # -------------------------------------------------
        # MAIN MENU
        # -------------------------------------------------

        if data == "main_menu":

            text = (
                f"👋 **Welcome {query.from_user.mention}!**\n\n"
                "**Main Menu**"
            )

            await query.message.edit_text(
                text,
                reply_markup=get_main_menu_keyboard()
            )

            await query.answer()


        # -------------------------------------------------
        # VIEW KEY
        # -------------------------------------------------

        elif data == "view_key":

            await query.answer()

            await render_key_page(
                query,
                user_id
            )


        # -------------------------------------------------
        # API DOCUMENTATION
        # -------------------------------------------------

        elif data == "api_docs":

            text = (
                "📚 **API Documentation**\n\n"

                "**Base URL:**\n"
                "`https://youtubeapi-india.herokuapp.com`\n\n"

                "**Primary API:**\n"
                "`https://youtubeapi-india.herokuapp.com`\n\n"

                "**Endpoint:**\n"
                "`GET /download`\n\n"

                "**Parameters:**\n"
                "`url`\n"
                "`type` → audio / video\n"
                "`api_key`\n\n"

                "**Example:**\n"
                "`/download?url=VIDEO_ID&type=audio&api_key=YOUR_KEY`\n\n"

                "A ready-to-use Python client is available below."
            )

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬇️ Download Youtube.py",
                        callback_data="dl_file"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="main_menu"
                    )
                ]
            ])

            await query.message.edit_text(
                text,
                reply_markup=keyboard
            )

            await query.answer()


        # -------------------------------------------------
        # RENEW / REVOKE
        # -------------------------------------------------

        elif data in [
            "action_renew",
            "action_revoke"
        ]:

            api_key, expiry_date, is_new = (
                await database.get_or_create_key(user_id)
            )

            if not is_new:

                now = datetime.now()

                days_left = max(
                    (expiry_date - now).days,
                    0
                )

                await query.answer(
                    f"⚠️ आपकी Key अभी valid है!\n"
                    f"नई Key {days_left} दिन बाद generate होगी।",
                    show_alert=True
                )

            else:

                await query.answer(
                    "✅ नई API Key generate कर दी गई है!",
                    show_alert=True
                )

                await render_key_page(
                    query,
                    user_id
                )


        # -------------------------------------------------
        # DOWNLOAD YOUTUBE.PY
        # -------------------------------------------------

        elif data == "dl_file":

            await query.answer(
                "Preparing Youtube.py...",
                show_alert=False
            )

            youtube_code = r'''import os
import re
import aiohttp
import yt_dlp

from typing import Union

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from py_yt import VideosSearch, Playlist


# =========================================================
# API CONFIG
# =========================================================

API_URL = os.environ.get(
    "API_URL",
    "https://youtubeapi-india.herokuapp.com"
)

API_KEY = os.environ.get(
    "API_KEY",
    "YOUR_API_KEY_HERE"
)


DOWNLOAD_DIR = "downloads"

os.makedirs(
    DOWNLOAD_DIR,
    exist_ok=True
)


# =========================================================
# TIME CONVERTER
# =========================================================

def time_to_seconds(time):

    if not time:
        return 0

    stringt = str(time)

    try:
        return sum(
            int(x) * 60 ** i
            for i, x in enumerate(
                reversed(stringt.split(":"))
            )
        )
    except Exception:
        return 0


# =========================================================
# VIDEO ID
# =========================================================

def extract_video_id(link):

    link = str(link).strip()

    if "v=" in link:
        return link.split(
            "v=",
            1
        )[1].split(
            "&",
            1
        )[0]

    if "youtu.be/" in link:
        return link.split(
            "youtu.be/",
            1
        )[1].split(
            "?",
            1
        )[0]

    if "/shorts/" in link:
        return link.split(
            "/shorts/",
            1
        )[1].split(
            "?",
            1
        )[0]

    return link


# =========================================================
# DOWNLOAD AUDIO
# =========================================================

async def download_song(link: str) -> Union[str, None]:

    video_id = extract_video_id(link)

    if not video_id:
        return None

    file_path = os.path.join(
        DOWNLOAD_DIR,
        f"{video_id}.mp3"
    )

    if (
        os.path.exists(file_path)
        and os.path.getsize(file_path) > 0
    ):
        return file_path

    try:

        async with aiohttp.ClientSession() as session:

            async with session.get(
                f"{API_URL}/download",
                params={
                    "url": video_id,
                    "type": "audio",
                    "api_key": API_KEY
                },
                timeout=aiohttp.ClientTimeout(
                    total=300
                )
            ) as response:

                if response.status != 200:
                    return None

                with open(
                    file_path,
                    "wb"
                ) as file:

                    async for chunk in response.content.iter_chunked(
                        131072
                    ):
                        file.write(chunk)

        if (
            os.path.exists(file_path)
            and os.path.getsize(file_path) > 0
        ):
            return file_path

        return None

    except Exception as e:

        print(
            f"Audio download error: {e}"
        )

        try:

            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception:
            pass

        return None


# =========================================================
# DOWNLOAD VIDEO
# =========================================================

async def download_video(link: str) -> Union[str, None]:

    video_id = extract_video_id(link)

    if not video_id:
        return None

    file_path = os.path.join(
        DOWNLOAD_DIR,
        f"{video_id}.mp4"
    )

    if (
        os.path.exists(file_path)
        and os.path.getsize(file_path) > 0
    ):
        return file_path

    try:

        async with aiohttp.ClientSession() as session:

            async with session.get(
                f"{API_URL}/download",
                params={
                    "url": video_id,
                    "type": "video",
                    "api_key": API_KEY
                },
                timeout=aiohttp.ClientTimeout(
                    total=600
                )
            ) as response:

                if response.status != 200:
                    return None

                with open(
                    file_path,
                    "wb"
                ) as file:

                    async for chunk in response.content.iter_chunked(
                        131072
                    ):
                        file.write(chunk)

        if (
            os.path.exists(file_path)
            and os.path.getsize(file_path) > 0
        ):
            return file_path

        return None

    except Exception as e:

        print(
            f"Video download error: {e}"
        )

        try:

            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception:
            pass

        return None


# =========================================================
# YOUTUBE API CLASS
# =========================================================

class YouTubeAPI:

    def __init__(self):

        self.base = (
            "https://www.youtube.com/watch?v="
        )

        self.regex = (
            r"(?:youtube\.com|youtu\.be)"
        )

        self.status = (
            "https://www.youtube.com/oembed?url="
        )

        self.listbase = (
            "https://youtube.com/playlist?list="
        )

        self.reg = re.compile(
            r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
        )


    async def exists(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        return bool(
            re.search(
                self.regex,
                link
            )
        )


    async def url(
        self,
        message_1: Message
    ):

        messages = [
            message_1
        ]

        if message_1.reply_to_message:
            messages.append(
                message_1.reply_to_message
            )

        for message in messages:

            if message.entities:

                for entity in message.entities:

                    if (
                        entity.type
                        == MessageEntityType.URL
                    ):

                        text = (
                            message.text
                            or message.caption
                            or ""
                        )

                        return text[
                            entity.offset:
                            entity.offset + entity.length
                        ]

            elif message.caption_entities:

                for entity in message.caption_entities:

                    if (
                        entity.type
                        == MessageEntityType.TEXT_LINK
                    ):
                        return entity.url

        return None


    async def details(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        if "&" in link:
            link = link.split("&")[0]

        results = VideosSearch(
            link,
            limit=1
        )

        result_data = (
            await results.next()
        ).get("result", [])

        if not result_data:
            raise ValueError(
                "YouTube video not found"
            )

        result = result_data[0]

        title = result["title"]
        duration_min = result["duration"]
        thumbnail = (
            result["thumbnails"][0]["url"]
            .split("?")[0]
        )

        vidid = result["id"]

        duration_sec = (
            time_to_seconds(
                duration_min
            )
            if duration_min
            else 0
        )

        return (
            title,
            duration_min,
            duration_sec,
            thumbnail,
            vidid
        )


    async def title(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        details = await self.details(
            link,
            videoid
        )

        return details[0]


    async def duration(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        details = await self.details(
            link,
            videoid
        )

        return details[1]


    async def thumbnail(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        details = await self.details(
            link,
            videoid
        )

        return details[3]


    async def video(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        try:

            downloaded_file = (
                await download_video(link)
            )

            if downloaded_file:
                return (
                    1,
                    downloaded_file
                )

            return (
                0,
                "Video download failed"
            )

        except Exception as e:

            return (
                0,
                f"Video download error: {e}"
            )


    async def playlist(
        self,
        link,
        limit,
        user_id,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.listbase + link

        if "&" in link:
            link = link.split("&")[0]

        try:

            playlist = await Playlist.get(
                link
            )

        except Exception:
            return []

        videos = (
            playlist.get("videos")
            or []
        )

        ids = []

        for data in videos[:limit]:

            if not data:
                continue

            vid = data.get("id")

            if vid:
                ids.append(vid)

        return ids


    async def track(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        if "&" in link:
            link = link.split("&")[0]

        results = VideosSearch(
            link,
            limit=1
        )

        result_data = (
            await results.next()
        ).get("result", [])

        if not result_data:
            return None, None

        result = result_data[0]

        title = result["title"]
        duration_min = result["duration"]
        vidid = result["id"]
        yturl = result["link"]

        thumbnail = (
            result["thumbnails"][0]["url"]
            .split("?")[0]
        )

        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }

        return (
            track_details,
            vidid
        )


    async def formats(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        if "&" in link:
            link = link.split("&")[0]

        ytdl_opts = {
            "quiet": True
        }

        formats_available = []

        try:

            with yt_dlp.YoutubeDL(
                ytdl_opts
            ) as ydl:

                result = ydl.extract_info(
                    link,
                    download=False
                )

                for fmt in result.get(
                    "formats",
                    []
                ):

                    try:

                        if "dash" in str(
                            fmt.get(
                                "format",
                                ""
                            )
                        ).lower():
                            continue

                        formats_available.append({
                            "format": fmt.get("format"),
                            "filesize": fmt.get("filesize"),
                            "format_id": fmt.get("format_id"),
                            "ext": fmt.get("ext"),
                            "format_note": fmt.get("format_note"),
                            "yturl": link,
                        })

                    except Exception:
                        continue

        except Exception:
            pass

        return (
            formats_available,
            link
        )


    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        if "&" in link:
            link = link.split("&")[0]

        results = VideosSearch(
            link,
            limit=10
        )

        result = (
            await results.next()
        ).get("result", [])

        if (
            not result
            or query_type >= len(result)
        ):
            raise ValueError(
                "YouTube result not found"
            )

        item = result[query_type]

        title = item["title"]
        duration_min = item["duration"]
        vidid = item["id"]

        thumbnail = (
            item["thumbnails"][0]["url"]
            .split("?")[0]
        )

        return (
            title,
            duration_min,
            thumbnail,
            vidid
        )


    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ):

        if videoid:
            link = self.base + link

        try:

            if video:
                downloaded_file = (
                    await download_video(link)
                )
            else:
                downloaded_file = (
                    await download_song(link)
                )

            if downloaded_file:
                return (
                    downloaded_file,
                    True
                )

            return (
                None,
                False
            )

        except Exception:

            return (
                None,
                False
            )


YouTube = YouTubeAPI()
'''

            file_bytes = io.BytesIO(
                youtube_code.encode("utf-8")
            )

            file_bytes.name = "Youtube.py"

            await client.send_document(
                chat_id=query.message.chat.id,
                document=file_bytes,
                caption=(
                    "✅ **Youtube.py ready!**\n\n"
                    "Set `API_URL` and `API_KEY` "
                    "in your music bot environment."
                )
            )

    except Exception as e:

        print(
            f"CALLBACK ERROR: {e}"
        )

        try:
            await query.answer(
                "⚠️ Something went wrong.",
                show_alert=True
            )
        except Exception:
            pass


# =========================================================
# HEROKU STARTUP
# =========================================================

if __name__ == "__main__":

    async def main():

        print(
            "Initializing database..."
        )

        await database.init_db()

        print(
            "Database initialized successfully!"
        )

        print(
            "Starting Telegram bot..."
        )

        await app.start()

        print(
            "Ronak API Bot Started Successfully!"
        )

        try:

            await idle()

        finally:

            print(
                "Stopping Telegram bot..."
            )

            await app.stop()

            print(
                "Bot stopped."
            )


    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        # Do not close Pyrogram's loop before its background cleanup completes.
        pass
