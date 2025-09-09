import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from jobs.gmail_job import main_job
from utils.gmail_utils import fetch_all_new_excels
from utils.excel_utils import process_excel
from utils.mail_utils import send_excel_email
import os

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# /start komutu
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Merhaba! Excel Mail Bot aktif. /process ile son gelen dosya işlenebilir.")

# /process komutu (manuel tetikleme)
@dp.message(Command("process"))
async def process_handler(message: types.Message):
    await message.answer("Gmail kontrol ediliyor...")
    excel_files = fetch_all_new_excels()

    if not excel_files:
        await message.answer("Henüz yeni Excel dosyası yok.")
        return

    for excel_file in excel_files:
        await message.answer(f"Dosya bulundu: {os.path.basename(excel_file)}. İşleme başlıyor...")
        result = process_excel(excel_file)
        if not result:
            await message.answer(f"{os.path.basename(excel_file)} için hiçbir grup satır bulunamadı.")
        else:
            for group, info in result.items():
                send_excel_email(info["email"], info["file"])
                await message.answer(f"{group.capitalize()} grubuna {info['rows']} satır gönderildi: {info['email']}")
            await message.answer(f"{os.path.basename(excel_file)} için tüm işlemler tamamlandı ✅")

# Bot başlat ve polling job ile çalıştır
async def main():
    print("Bot ve Gmail otomatik polling + günlük temp temizleme başlatılıyor...")
    await asyncio.gather(
        dp.start_polling(bot),
        main_job()
    )

if __name__ == "__main__":
    asyncio.run(main())
