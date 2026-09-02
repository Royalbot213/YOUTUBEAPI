import os
import re
import hmac
import hashlib
import base64
import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import yt_dlp

APP_VERSION = "1.0.0"
DOWNLOAD_DIR = "downloads"
KEY_SECRET = os.environ.get("API_KEY_SECRET") or os.environ.get("BOT_TOKEN", "change-this-secret")
KEY_DAYS = 30

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="Fresh YouTube API",
    description="YouTube audio/video download API",
    version=APP_VERSION,
)


def _period(now: datetime):
    # A deterministic 30-day key period shared by bot and web dynos.
    epoch = datetime(2026, 1, 1, tzinfo=timezone.utc)
    elapsed = max((now - epoch).total_seconds(), 0)
    number = int(elapsed // (KEY_DAYS * 86400))
    start = epoch + timedelta(days=number * KEY_DAYS)
    expiry = start + timedelta(days=KEY_DAYS)
    return start, expiry


def make_api_key(user_id: int, now: datetime | None = None) -> tuple[str, datetime]:
    now = now or datetime.now(timezone.utc)
    start, expiry = _period(now)
    payload = f"{user_id}:{start.strftime('%Y%m%d')}".encode()
    digest = hmac.new(KEY_SECRET.encode(), payload, hashlib.sha256).digest()[:12]
    token = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return f"RonakBots_{user_id}_{token}", expiry


def verify_api_key(api_key: str) -> tuple[bool, str]:
    if not api_key or not api_key.startswith("RonakBots_"):
        return False, "Invalid API Key"

    parts = api_key.split("_")
    if len(parts) != 3:
        return False, "Invalid API Key"

    try:
        user_id = int(parts[1])
    except ValueError:
        return False, "Invalid API Key"

    now = datetime.now(timezone.utc)
    expected, expiry = make_api_key(user_id, now)
    expected_token = expected.rsplit("_", 1)[1]

    if now >= expiry:
        return False, "API Key expired. Get a new key from the Telegram bot."

    if not hmac.compare_digest(parts[2], expected_token):
        return False, "Invalid API Key"

    return True, "Valid"


def extract_video_id(url: str) -> str:
    url = url.strip()

    patterns = [
        r"(?:v=)([A-Za-z0-9_-]{6,})",
        r"youtu\.be/([A-Za-z0-9_-]{6,})",
        r"youtube\.com/shorts/([A-Za-z0-9_-]{6,})",
        r"youtube\.com/embed/([A-Za-z0-9_-]{6,})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    if re.fullmatch(r"[A-Za-z0-9_-]{6,}", url):
        return url

    raise HTTPException(status_code=400, detail="Invalid YouTube URL")


def cleanup_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Fresh YouTube API",
        "version": APP_VERSION,
        "health": "/health",
        "docs": "/docs",
        "download": "/download",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/download")
async def download(
    url: str,
    type: str,
    api_key: str,
    background_tasks: BackgroundTasks,
):
    valid, message = verify_api_key(api_key)
    if not valid:
        raise HTTPException(status_code=403, detail=message)

    if type not in ("audio", "video"):
        raise HTTPException(status_code=400, detail="type must be audio or video")

    video_id = extract_video_id(url)

    if type == "audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{DOWNLOAD_DIR}/{video_id}.%(ext)s",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
        media_type = "audio/mpeg"
        extension = "mp3"
    else:
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": f"{DOWNLOAD_DIR}/{video_id}.%(ext)s",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "merge_output_format": "mp4",
        }
        media_type = "video/mp4"
        extension = "mp4"

    def do_download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}",
                download=True,
            )
            prepared = ydl.prepare_filename(info)

            if type == "audio":
                return os.path.splitext(prepared)[0] + ".mp3"

            mp4 = os.path.splitext(prepared)[0] + ".mp4"
            if os.path.exists(mp4):
                return mp4
            return prepared

    try:
        filename = await asyncio.to_thread(do_download)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Download Error: {exc}")

    if not filename or not os.path.exists(filename):
        raise HTTPException(status_code=500, detail="Downloaded file was not found")

    background_tasks.add_task(cleanup_file, filename)

    return FileResponse(
        filename,
        media_type=media_type,
        filename=f"{video_id}.{extension}",
        background=background_tasks,
    )
