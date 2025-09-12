# jobs/scheduled_tasks.py
# PASİF EDİLDİ
#zamanlayıcıyı devre dışı bırakır hem de loglara pasif durumu yazarak ileride hatırlamanızı sağlar. Ayrıca await asyncio.sleep(60) ile CPU kullanımını da azaltmış olur
#GEREKSİZ, ZATEN TELE BİLDİRİM GELİYOR 
#FUL OTO PARA KAYBETTİRİR, sonranin işi bu
import asyncio
import aioschedule
import logging
from config import ADMIN_IDS
from utils import email_utils, file_utils

logger = logging.getLogger(__name__)

async def scheduled_email_check(bot):
    try:
        # Zamanlayıcı pasif - işlem yapma
        logger.info("E-posta kontrolü pasif durumda")
        return []
    except Exception as e:
        logger.error(f"E-posta kontrolü sırasında hata oluştu: {e}")
        return []

async def scheduled_cleanup():
    try:
        # Zamanlayıcı pasif - işlem yapma
        logger.info("Temizleme işlemi pasif durumda")
    except Exception as e:
        logger.error(f"Dosya temizleme sırasında hata oluştu: {e}")

def schedule_email_check(bot):
    """Wrapper function for aioschedule"""
    asyncio.create_task(scheduled_email_check(bot))

def schedule_cleanup():
    """Wrapper function for aioschedule"""
    asyncio.create_task(scheduled_cleanup())

async def scheduler(bot):
    # Zamanlayıcıları yorum satırına al veya kaldır
    # aioschedule.every(10).minutes.do(schedule_email_check, bot)
    # aioschedule.every().day.at("23:59").do(schedule_cleanup)

    logger.info("Zamanlayıcı PASİF durumda - tüm görevler devre dışı")

    while True:
        try:
            # Zamanlayıcıyı çalıştırma, sadece bekle
            await asyncio.sleep(60)  # CPU kullanımını azaltmak için daha uzun bekleme
        except Exception as e:
            logger.error(f"Zamanlayıcı hatası: {e}")
            await asyncio.sleep(60)
