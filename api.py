import os
import asyncio
import re

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import yt_dlp

import database

app = FastAPI(
    title="Ronak Fast API",
    description="Fast YouTube Audio & Video Download API",
    version="2.1.0",
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


@app.on_event("startup")
async def startup():
    await database.init_db()


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Ronak Fast API",
        "version": "2.1.0",
        "docs": "/docs",
        "health": "/health",
        "download_endpoint": "/download",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


def delete_file(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def extract_video_id(url: str) -> str:
    value = url.strip()

    patterns = [
        r"(?:v=)([A-Za-z0-9_-]{6,})",
        r"(?:youtu\.be/)([A-Za-z0-9_-]{6,})",
        r"(?:youtube\.com/shorts/)([A-Za-z0-9_-]{6,})",
        r"(?:youtube\.com/embed/)([A-Za-z0-9_-]{6,})",
    ]

    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)

    # Allow a raw YouTube video ID.
    if re.fullmatch(r"[A-Za-z0-9_-]{6,}", value):
        return value

    return ""


@app.get("/download")
async def download_media(
    url: str,
    type: str,
    api_key: str,
    background_tasks: BackgroundTasks,
):
    is_valid, msg = await database.verify_key(api_key)
    if not is_valid:
        raise HTTPException(status_code=403, detail=msg)

    if type not in ("audio", "video"):
        raise HTTPException(
            status_code=400,
            detail="type must be audio or video",
        )

    video_id = extract_video_id(url)
    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL or video ID",
        )

    source_url = f"https://www.youtube.com/watch?v={video_id}"

    if type == "audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{DOWNLOAD_DIR}/{video_id}.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "nocheckcertificate": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
    else:
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": f"{DOWNLOAD_DIR}/{video_id}.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "nocheckcertificate": True,
            "merge_output_format": "mp4",
        }

    def extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source_url, download=True)
            prepared = ydl.prepare_filename(info)

            if type == "audio":
                filename = os.path.splitext(prepared)[0] + ".mp3"
            else:
                base = os.path.splitext(prepared)[0]
                mp4_file = base + ".mp4"
                filename = mp4_file if os.path.exists(mp4_file) else prepared

            return filename

    try:
        filename = await asyncio.to_thread(extract)

        if not filename or not os.path.isfile(filename):
            raise HTTPException(
                status_code=500,
                detail="Download completed but output file was not found",
            )

        background_tasks.add_task(delete_file, filename)

        media_type = "audio/mpeg" if type == "audio" else "video/mp4"

        return FileResponse(
            filename,
            media_type=media_type,
            filename=os.path.basename(filename),
            background=background_tasks,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Download Error: {str(e)}",
        )
