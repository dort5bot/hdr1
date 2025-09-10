import asyncio
import logging
from aiogram import Bot, Dispatcher
from handlers.commands import router as commands_router
from handlers.email_handlers import router as email_router
from jobs.scheduled_tasks import scheduler
from config import TELEGRAM_BOT, ADMIN_IDS, TEMP_DIR

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_BOT)
dp = Dispatcher()

# Include all routers
dp.include_router(commands_router)
dp.include_router(email_router)

async def on_startup():
    """Run on bot startup"""
    # Create temp directory if it doesn't exist
    import os
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Start scheduler
    asyncio.create_task(scheduler())
    
    # Send startup message to admins
    for admin_id in ADMIN_IDS:
        await bot.send_message(admin_id, "HIDIR Botu başlatıldı.")

async def main():
    # Set up startup function
    dp.startup.register(on_startup)
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
