#jobs/gmail_job.py
import asyncio
import time
from utils.gmail_utils import fetch_latest_excel
from utils.excel_utils import process_excel
from utils.mail_utils import send_excel_email
from aiogram import Bot
import os

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = Bot(token=BOT_TOKEN)
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")  # Telegram üzerinden log almak için

CHECK_INTERVAL = 300  # 5 dk

async def send_telegram_message(text):
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
    except Exception as e:
        print(f"[ERROR] Telegram mesaj gönderilemedi: {e}")


async def polling_loop():
    while True:
        await send_telegram_message("Gmail kontrol başlatıldı...")
        excel_file = fetch_latest_excel()
        if excel_file:
            await send_telegram_message(f"Dosya bulundu: {os.path.basename(excel_file)}. İşleme başlıyor...")
            result = process_excel(excel_file)
            if not result:
                await send_telegram_message("Hiçbir grup için satır bulunamadı.")
            else:
                for group, info in result.items():
                    send_excel_email(info["email"], info["file"])
                    await send_telegram_message(f"{group.capitalize()} grubuna {info['rows']} satır gönderildi: {info['email']}")
                await send_telegram_message("Tüm işlem tamamlandı ✅")
        else:
            await send_telegram_message("Henüz yeni dosya yok.")

        await asyncio.sleep(CHECK_INTERVAL)  # Belirlenen süre bekle
