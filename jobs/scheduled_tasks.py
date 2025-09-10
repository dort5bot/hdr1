import asyncio
import aioschedule
import logging
from config import ADMIN_IDS
from utils import email_utils, file_utils
from main import bot

logger = logging.getLogger(__name__)

async def scheduled_email_check():
    """Check for new emails periodically"""
    new_files = await email_utils.check_email()
    if new_files:
        for admin_id in ADMIN_IDS:
            await bot.send_message(admin_id, f"Yeni mail var: {len(new_files)} Excel ekli")

async def scheduler():
    """Run scheduled tasks"""
    aioschedule.every(10).minutes.do(scheduled_email_check)
    aioschedule.every().day.at("23:59").do(file_utils.cleanup_temp)
    
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)