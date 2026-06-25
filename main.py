import os
from dotenv import load_dotenv

load_dotenv()

import asyncio
import logging
from aiogram import Bot, Dispatcher
from handlers import listener, speaker, organizer
from database import db_manager


ORGANIZER_ID = os.getenv("ORGANIZER_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Включаем логирование, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)

async def main():
    db_manager.init_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем модули (роутеры) всех разработчиков
    dp.include_router(listener.router)
    dp.include_router(speaker.router)
    dp.include_router(organizer.router)

    print("🚀 Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
