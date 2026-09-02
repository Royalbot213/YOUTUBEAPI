# YOUTUBEAPI — Heroku Ready

FastAPI + Telegram bot project, configured for one-click Heroku deployment.

## 🚀 Deploy to Heroku

> **Important:** The button works after this repository is pushed to GitHub and the URL below is changed to your real GitHub repository.

### One-click button

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/YOUR_USERNAME/YOUR_REPOSITORY)

### Replace the button URL

Change:

```text
https://github.com/YOUR_USERNAME/YOUR_REPOSITORY
```

to your actual public GitHub repository, for example:

```text
https://github.com/myname/YOUTUBEAPI
```

Then the final Deploy URL is:

```text
https://heroku.com/deploy?template=https://github.com/myname/YOUTUBEAPI
```

## ⚙️ Required Heroku Config Vars

The Deploy button will request these values from `app.json`:

| Variable | Required | Where to get it |
|---|---|---|
| `API_ID` | Yes | `my.telegram.org` |
| `API_HASH` | Yes | `my.telegram.org` |
| `BOT_TOKEN` | Yes | `@BotFather` on Telegram |
| `RONAK_API_URL` | No | Public API URL, if needed |
| `RONAK_API_KEY` | No | Optional API key used by the client |

Do **not** put real Telegram credentials directly into the source code.

## 🛠️ Heroku deployment

1. Push this project to a **public GitHub repository**.
2. Make sure these files are in the repository root:
   - `app.json`
   - `Procfile`
   - `requirements.txt`
   - `apt.txt`
   - `bot.py`
   - `api.py`
3. Open the Deploy button above.
4. Enter the required Config Vars.
5. Choose an app name and click **Deploy app**.
6. After deployment, open **Resources** and make sure the `web` dyno is enabled.
7. Open **View logs** if you want to verify the bot/API startup.

## 🌐 API

The Heroku web process starts both:

- Telegram bot: `bot.py`
- FastAPI server: `api:app`

The FastAPI server listens on Heroku's `$PORT` automatically.

After deployment, your API base URL will be:

```text
https://YOUR-APP-NAME.herokuapp.com
```

## 🔐 Security

Never commit:

- Telegram `BOT_TOKEN`
- Telegram `API_HASH`
- private API keys
- session strings

If a real token was previously exposed in a repository, revoke/rotate it before deploying.
