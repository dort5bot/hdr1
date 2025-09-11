import asyncio
import aioschedule
import logging
from config import ADMIN_IDS
from utils import email_utils, file_utils

logger = logging.getLogger(__name__)

async def scheduled_email_check(bot):
    """Check for new emails periodically"""
    try:
        new_files = await email_utils.check_email()
        if new_files:
            message = f"Yeni mail var: {len(new_files)} Excel ekli"
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(admin_id, message)
                except Exception as e:
                    logger.error(f"Admin mesajı gönderilemedi ({admin_id}): {e}")
        return new_files
    except Exception as e:
        logger.error(f"E-posta kontrolü sırasında hata oluştu: {e}")
        return []

async def scheduled_cleanup():
    """Cleanup temporary files"""
    try:
        await file_utils.cleanup_temp()
        logger.info("Geçici dosyalar temizlendi")
    except Exception as e:
        logger.error(f"Dosya temizleme sırasında hata oluştu: {e}")

async def scheduler(bot):
    """Run scheduled tasks with bot instance"""
    # Bot parametresini partial fonksiyonla geçmek yerine lambda kullanıyoruz
    aioschedule.every(10).minutes.do(
        lambda: asyncio.create_task(scheduled_email_check(bot))
    )
    aioschedule.every().day.at("23:59").do(
        lambda: asyncio.create_task(scheduled_cleanup())
    )
    
    logger.info("Zamanlayıcı başlatıldı")
    
    while True:
        try:
            await aioschedule.run_pending()
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Zamanlayıcı hatası: {e}")
            await asyncio.sleep(60)  # Hata durumunda 60 saniye bekle
