import asyncio
import os

import yaml
from src.bot.telegram_bot import TelegramBot
from src.db.db_manager import init_db


async def main():
    TOKEN = os.getenv("API_KEY")

    if not TOKEN:
        raise ValueError("API_KEY is missing in the config file")

    await init_db()
    bot = TelegramBot(TOKEN)
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
