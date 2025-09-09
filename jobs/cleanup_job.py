import os
import asyncio
import datetime
import shutil

TEMP_DIR = os.path.join("data", "temp")

async def cleanup_temp_daily():
    """
    Gün sonunda temp/ klasörünü temizler.
    """
    while True:
        now = datetime.datetime.now()
        # Bir sonraki günün 00:00:01 zamanını hesapla
        next_day = datetime.datetime.combine(now.date() + datetime.timedelta(days=1),
                                             datetime.time(hour=0, minute=0, second=1))
        wait_seconds = (next_day - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        # Temp klasörünü temizle
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"[ERROR] {file_path} silinemedi: {e}")

        print("[INFO] Temp klasörü temizlendi ✅")
