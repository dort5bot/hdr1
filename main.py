import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from jobs.scheduled_tasks import scheduler
from config import (
    TELEGRAM_BOT,
    ADMIN_IDS,
    TEMP_DIR,
    USE_WEBHOOK,
    WEBHOOK_URL,
    WEBHOOK_PATH,
    WEBHOOK_HOST,
    WEBHOOK_PORT,
)
from utils.handler_loader import setup_handlers

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_BOT)
dp = Dispatcher()


async def on_startup():
    """Run on bot startup"""
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Start scheduler
    asyncio.create_task(scheduler())

    # Load all handlers automatically
    loaded = await setup_handlers(dp, "handlers")
    logger.info(f"{loaded} handler(s) loaded successfully")

    # Set webhook if using webhook mode
    # Set webhook if using webhook mode
    if USE_WEBHOOK:
        path = f"{WEBHOOK_PATH}/{TELEGRAM_BOT}"
    
        # server hangi path'i dinleyecek
        webhook_requests_handler.register(app, path=path)
    
        # Telegram'a hangi URL'yi set edecek
        await bot.set_webhook(f"{WEBHOOK_URL}{path}")
        logger.info("Webhook set successfully")

    # Send startup message to admins
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "✅ HIDIR Botu başlatıldı.")
        except Exception as e:
            logger.error(f"Admin mesajı gönderilemedi: {e}")


async def on_shutdown():
    """Run on bot shutdown"""
    if USE_WEBHOOK:
        await bot.delete_webhook()
    await bot.session.close()
    logger.info("Bot shutdown completed")


async def main_webhook():
    """Webhook mode"""
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )

    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    try:
        await web._run_app(app, host=WEBHOOK_HOST, port=WEBHOOK_PORT)
    except Exception as e:
        logger.error(f"Webhook server error: {e}")


async def main_polling():
    """Polling mode"""
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Polling error: {e}")


async def main():
    """Main function"""
    if USE_WEBHOOK:
        logger.info("Starting in WEBHOOK mode")
        await main_webhook()
    else:
        logger.info("Starting in POLLING mode")
        await main_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot manually stopped")
