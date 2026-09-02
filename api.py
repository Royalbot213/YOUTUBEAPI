import os
import asyncio

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import yt_dlp

import database


app = FastAPI(
    title="Ronak Fast API",
    description="Fast YouTube Audio & Video Download API",
    version="2.0.0"
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# =========================
# DATABASE STARTUP
# =========================

@app.on_event("startup")
async def startup():
    await database.init_db()


# =========================
# ROOT / STATUS
# =========================

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Ronak Fast API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "download_endpoint": "/download"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }


# =========================
# DELETE DOWNLOADED FILE
# =========================

def delete_file(path: str):
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


# =========================
# DOWNLOAD API
# =========================

@app.get("/download")
async def download_media(
    url: str,
    type: str,
    api_key: str,
    background_tasks: BackgroundTasks
):

    # Validate API key
    is_valid, msg = await database.verify_key(api_key)

    if not is_valid:
        raise HTTPException(
            status_code=403,
            detail=msg
        )

    # Validate type
    if type not in ["audio", "video"]:
        raise HTTPException(
            status_code=400,
            detail="type must be audio or video"
        )

    # Extract YouTube video ID
    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]

    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]

    else:
        video_id = url.strip()

    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL"
        )

    # =========================
    # AUDIO
    # =========================

    if type == "audio":

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{DOWNLOAD_DIR}/{video_id}.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "nocheckcertificate": True,
        }

    # =========================
    # VIDEO
    # =========================

    else:

        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": f"{DOWNLOAD_DIR}/{video_id}.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "merge_output_format": "mp4",
            "nocheckcertificate": True,
        }

    # =========================
    # DOWNLOAD
    # =========================

    def extract():

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}",
                download=True
            )

            filename = ydl.prepare_filename(info)

            # Video merge can change extension to mp4
            if type == "video":

                base = os.path.splitext(filename)[0]
                mp4_file = base + ".mp4"

                if os.path.exists(mp4_file):
                    filename = mp4_file

            return filename

    try:

        filename = await asyncio.to_thread(extract)

        if not filename or not os.path.exists(filename):

            raise HTTPException(
                status_code=500,
                detail="Download completed but file was not found"
            )

        # Delete after response is finished
        background_tasks.add_task(
            delete_file,
            filename
        )

        return FileResponse(
            filename,
            media_type="application/octet-stream",
            filename=os.path.basename(filename),
            background=background_tasks
        )

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Download Error: {str(e)}"
    )
