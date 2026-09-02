import os
import secrets
from datetime import datetime, timedelta

import aiosqlite

DB_NAME = os.environ.get("DB_NAME", "ronak_system.db")


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                api_key TEXT UNIQUE NOT NULL,
                expiry_date TEXT NOT NULL
            )
        """)
        await db.commit()


async def get_or_create_key(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT api_key, expiry_date FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()

        now = datetime.now()

        if row:
            api_key, expiry_str = row
            expiry_date = datetime.fromisoformat(expiry_str)

            if now >= expiry_date:
                new_key = f"RonakBots_{secrets.token_hex(8)}"
                new_expiry = now + timedelta(days=30)

                await db.execute(
                    """
                    UPDATE users
                    SET api_key = ?, expiry_date = ?
                    WHERE user_id = ?
                    """,
                    (new_key, new_expiry.isoformat(), user_id)
                )
                await db.commit()

                return new_key, new_expiry, True

            return api_key, expiry_date, False

        new_key = f"RonakBots_{secrets.token_hex(8)}"
        new_expiry = now + timedelta(days=30)

        await db.execute(
            """
            INSERT INTO users (user_id, api_key, expiry_date)
            VALUES (?, ?, ?)
            """,
            (user_id, new_key, new_expiry.isoformat())
        )
        await db.commit()

        return new_key, new_expiry, True


async def verify_key(api_key: str):
    if not api_key:
        return False, "API Key is required"

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT expiry_date FROM users WHERE api_key = ?",
            (api_key,)
        )
        row = await cursor.fetchone()

        if not row:
            return False, "Invalid API Key"

        try:
            expiry_date = datetime.fromisoformat(row[0])
        except (TypeError, ValueError):
            return False, "Invalid API Key data"

        if datetime.now() >= expiry_date:
            return False, "API Key Expired! Please get a new key from the bot."

        return True, "Valid"
