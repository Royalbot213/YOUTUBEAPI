# YOUTUBEAPI — Heroku Ready

FastAPI + Telegram API-key bot.

## Deploy button

After pushing this project to GitHub, use:

`https://heroku.com/deploy?template=https://github.com/YOUR_USERNAME/YOUR_REPOSITORY`

For the README button, replace `YOUR_USERNAME/YOUR_REPOSITORY` with your actual GitHub repository.

## Required Config Vars

- `API_ID`
- `API_HASH`
- `BOT_TOKEN`

The Deploy button will ask for these values.

## Important

Telegram credentials should be stored only in Heroku Config Vars, not in source code. If the credentials in the original ZIP were real, rotate the API hash/token before deploying.
