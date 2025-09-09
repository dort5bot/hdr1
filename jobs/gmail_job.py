import asyncio
from utils.gmail_utils import fetch_all_new_excels
from utils.excel_utils import process_excel
from utils.mail_utils import send_excel_email
from aiogram import Bot
import os

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = Bot(token=BOT_TOKEN)
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")  # Telegram log için

CHECK_INTERVAL = 300  # 5 dakika

async def send_telegram_message(text):
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
    except Exception as e:
        print(f"[ERROR] Telegram mesaj gönderilemedi: {e}")


async def polling_loop():
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
