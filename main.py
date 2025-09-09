import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import os

from utils.excel_utils import process_excel
from utils.mail_utils import send_excel_email
from utils.gmail_utils import fetch_latest_excel

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# /start komutu
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Merhaba! Excel Mail Bot aktif. /process ile son gelen dosya işlenebilir.")

# /process komutu
@dp.message(Command("process"))
async def process_handler(message: types.Message):
    await message.answer("Gmail kontrol ediliyor...")
    excel_file = fetch_latest_excel()
    if not excel_file:
        await message.answer("Henüz gelen Excel dosyası yok.")
        return

    await message.answer(f"Dosya bulundu: {os.path.basename(excel_file)}. İşleme başlıyor...")
    result = process_excel(excel_file)

    if not result:
        await message.answer("Hiçbir grup için satır bulunamadı.")
        return

    for group, info in result.items():
        send_excel_email(info["email"], info["file"])
        await message.answer(f"{group.capitalize()} grubuna {info['rows']} satır gönderildi: {info['email']}")

    await message.answer("Tüm işlem tamamlandı ✅")

# Bot başlat
async def main():
    print("Bot çalışıyor...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
