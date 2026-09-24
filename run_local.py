# локальный запуск через polling, без webhook
import os
import sys
import asyncio
from dotenv import load_dotenv
from telegram import Update

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from app.bot import create_application

async def main():
    application = create_application()
    
    print("Бот запущен в режиме polling...")
    print("Нажмите Ctrl+C для остановки")
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    finally:
        await application.updater.stop()
        await application.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен")
    except Exception as e:
        print(f"Ошибка: {e}")
        raise
