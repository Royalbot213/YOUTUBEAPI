# 🎬 Fresh YouTube API + Telegram Bot

FastAPI YouTube Audio/Video API with a Telegram bot for API-key generation.

## 🚀 Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://www.heroku.com/deploy?template=https://github.com/Royalbot213/YOUTUBEAPI)

## ✨ Features

- YouTube → MP3
- YouTube → MP4
- 30-day API keys
- Telegram bot
- FastAPI + Swagger
- FFmpeg
- No SQLite/shared-dyno database

## 🔐 Required Config Vars

- `BOT_TOKEN` — Telegram BotFather token
- `API_KEY_SECRET` — secret for API-key generation/verification
- `API_BASE_URL` — optional public app URL

## ⚙️ Processes

web: `uvicorn api:app --host 0.0.0.0 --port $PORT`

worker: `python bot.py`

## 🧪 Test

`https://YOUR-APP.herokuapp.com/health`

Expected:

```json
{"status":"ok"}
```

Swagger: `/docs`

## 📥 Download

GET `/download`

Parameters:

- `url`
- `type=audio` or `type=video`
- `api_key`

## 🤖 Telegram

Send `/start` to the bot to receive your API key.

## 📁 Project Structure

```text
api.py
bot.py
requirements.txt
Procfile
Aptfile
runtime.txt
app.json
README.md
.gitignore
```

Never upload bot tokens or secrets to GitHub. Use Heroku Config Vars.
