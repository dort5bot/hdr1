import asyncio
import datetime
import os
from utils.gmail_utils import fetch_all_new_excels
from utils.excel_utils import process_excel
from utils.mail_utils import send_excel_email
from aiogram import Bot

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
bot = Bot(token=BOT_TOKEN)

TEMP_DIR = os.path.join("data", "temp")
CHECK_INTERVAL = 300  # 5 dakika

async def send_telegram_message(text):
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
    except Exception as e:
        print(f"[ERROR] Telegram mesaj gönderilemedi: {e}")

async def daily_temp_cleanup():
    """
    Her gün 23:59'da temp klasörünü temizler.
    """
    while True:
        now = datetime.datetime.now()
        next_cleanup = datetime.datetime.combine(now.date(), datetime.time(hour=23, minute=59, second=0))
        if now > next_cleanup:
            next_cleanup += datetime.timedelta(days=1)
        wait_seconds = (next_cleanup - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        # Temp temizleme
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    import shutil
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"[ERROR] {file_path} silinemedi: {e}")

        await send_telegram_message("[INFO] Temp klasörü temizlendi ✅")

async def polling_loop():
    """
    Gmail kontrol döngüsü, gelen tüm Excel dosyalarını işler.
    """
    while True:
        await send_telegram_message("Gmail kontrol başlatıldı...")
        excel_files = fetch_all_new_excels()

        if not excel_files:
            await send_telegram_message("Henüz yeni Excel dosyası yok.")
        else:
            for excel_file in excel_files:
                await send_telegram_message(f"Dosya bulundu: {os.path.basename(excel_file)}. İşleme başlıyor...")
                result = process_excel(excel_file)
                if not result:
                    await send_telegram_message(f"{os.path.basename(excel_file)} için hiçbir grup satır bulunamadı.")
                else:
                    for group, info in result.items():
                        send_excel_email(info["email"], info["file"])
                        await send_telegram_message(f"{group.capitalize()} grubuna {info['rows']} satır gönderildi: {info['email']}")
                    await send_telegram_message(f"{os.path.basename(excel_file)} için tüm işlemler tamamlandı ✅")

        await asyncio.sleep(CHECK_INTERVAL)

async def main_job():
    await asyncio.gather(
        polling_loop(),
        daily_temp_cleanup()
    )
