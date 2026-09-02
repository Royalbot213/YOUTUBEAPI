# Fresh YouTube API + Telegram Bot

A fresh Heroku-ready project containing:

- FastAPI web API
- Telegram bot
- 30-day deterministic API keys
- YouTube audio -> MP3
- YouTube video -> MP4
- FFmpeg
- No SQLite, so web and worker dynos do not need shared storage

## Heroku Config Vars

Required:

- `BOT_TOKEN`
- `API_KEY_SECRET`

`API_KEY_SECRET` can be any long random secret.

Optional:

- `API_BASE_URL` = your Heroku app URL

Example:

`https://your-app-name.herokuapp.com`

## Deploy

1. Create a new Heroku app.
2. Deploy this project.
3. Make sure the Apt buildpack is installed and `Aptfile` contains `ffmpeg`.
4. Set the Config Vars.
5. Scale:
   - web = 1
   - worker = 1

The Procfile already contains both processes.

## Test

Open:

`/health`

Expected:

`{"status":"ok"}`

Open `/docs` for Swagger.

## API

GET `/download`

Parameters:

- `url`
- `type=audio` or `type=video`
- `api_key`

Example:

`/download?url=https://www.youtube.com/watch?v=VIDEO_ID&type=audio&api_key=YOUR_KEY`

## Telegram

Send `/start` to the bot.

No `API_ID` or `API_HASH` is required because this version uses the Bot API through `python-telegram-bot`.
