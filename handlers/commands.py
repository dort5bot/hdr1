#handlers/commands.py
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
import logging
from config import source_emails, groups, ADMIN_IDS
from utils import email_utils, excel_processor, file_utils
import datetime
import time
import psutil
import os
import json
from dotenv import load_dotenv

router = Router()
logger = logging.getLogger(__name__)

# Bot başlangıç zamanı
BOT_START_TIME = time.time()

@router.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    await message.answer(
        "HIDIR Botuna Hoşgeldiniz!\n\n"
        "📧 **Mail Komutları:**\n"
        "/checkmail - Manuel mail kontrolü\n"
        "/process - Excel işleme\n\n"
        "👥 **Grup Yönetimi:**\n"
        "/gruplar - Tüm grupları listele\n"
        "/grupekle - Yeni grup ekle\n"
        "/grupsil - Grup sil\n"
        "/grupduzenle - Grup düzenle\n"
        "/grupyedekle - Grupları JSON olarak göster\n"
        "/grupsifirla - Grupları sıfırla\n\n"
        "⚙️ **Sistem Komutları:**\n"
        "/cleanup - Temp temizle\n"
        "/stats - İstatistikler\n"
        "/health - Sistem durumu\n"
        "/ping - Yanıt süresi\n"
        "/status - Detaylı durum"
    )

@router.message(Command("health"))
async def health_check(message: types.Message):
    """Bot sağlık durumunu kontrol eder"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    try:
        # Basit bir health check
        await message.answer("✅ Bot çalışıyor ve sağlıklı!")
        
    except Exception as e:
        await message.answer(f"❌ Health check hatası: {str(e)}")

@router.message(Command("ping"))
async def ping(message: types.Message):
    """Bot yanıt süresini test eder"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    start_time = time.time()
    pong_message = await message.answer("🏓 Pong!")
    end_time = time.time()
    
    response_time = round((end_time - start_time) * 1000, 2)
    await pong_message.edit_text(f"🏓 Pong! Yanıt süresi: {response_time}ms")

@router.message(Command("status"))
async def status_check(message: types.Message):
    """Sistem durumunu gösterir"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    try:
        # Sistem bilgileri
        uptime = time.time() - BOT_START_TIME
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # CPU ve memory kullanımı
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Process bilgileri
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB cinsinden
        
        status_message = (
            "📊 **Sistem Durumu**\n\n"
            f"⏰ **Çalışma Süresi:** {int(hours)}sa {int(minutes)}dk {int(seconds)}sn\n"
            f"🖥️ **CPU Kullanımı:** {cpu_percent}%\n"
            f"💾 **Bellek Kullanımı:** {memory.percent}%\n"
            f"📦 **Disk Kullanımı:** {disk.percent}%\n"
            f"🤖 **Bot Bellek:** {memory_usage:.2f} MB\n"
            f"📧 **Kaynak Mailler:** {len(source_emails)}\n"
            f"👥 **Gruplar:** {len(groups)}\n"
            f"👑 **Adminler:** {len(ADMIN_IDS)}"
        )
        
        await message.answer(status_message)
        
    except Exception as e:
        await message.answer(f"❌ Status check hatası: {str(e)}")

@router.message(Command("kay"))
async def cmd_kay(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    if not source_emails:
        await message.answer("Kaynak mail adresi bulunamadı.")
        return
        
    response = "📧 **Kaynak Mail Adresleri:**\n\n"
    for i, email in enumerate(source_emails, 1):
        response += f"{i}. `{email}`\n"
        
    await message.answer(response)

@router.message(Command("kayek"))
async def cmd_kayek(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Kullanım: /kayek <email_adresi>")
        return
        
    new_email = parts[1]
    if new_email in source_emails:
        await message.answer(f"❌ `{new_email}` zaten kayıtlı.")
        return
        
    source_emails.append(new_email)
    await message.answer(f"✅ `{new_email}` kaynak mail olarak eklendi.")

@router.message(Command("kaysil"))
async def cmd_kaysil(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Kullanım: /kaysil <sıra_no>")
        return
        
    try:
        index = int(parts[1]) - 1
        if index < 0 or index >= len(source_emails):
            await message.answer("❌ Geçersiz sıra numarası.")
            return
            
        removed_email = source_emails.pop(index)
        await message.answer(f"✅ `{removed_email}` kaynak mail olarak silindi.")
    except ValueError:
        await message.answer("❌ Geçersiz sıra numarası.")

@router.message(Command("gr"))
async def cmd_gr(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    if not groups:
        await message.answer("❌ Grup bulunamadı.")
        return
        
    response = "👥 **Gruplar:**\n\n"
    for i, group in enumerate(groups, 1):
        cities = ", ".join(group["cities"])
        response += f"{i}. **{group['name']}**\n"
        response += f"   📍 Şehirler: {cities}\n"
        response += f"   📧 Email: `{group['email']}`\n\n"
        
    await message.answer(response)

@router.message(Command("grek"))
async def cmd_grek(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.answer("Kullanım: /grek <grup_adi> <iller> <email>")
        await message.answer("Örnek: /grek ege izmir,aydın,muğla ege@example.com")
        return
        
    group_name = parts[1]
    cities = [c.strip() for c in parts[2].split(",")]
    group_email = parts[3]
    
    # Check if group already exists
    for i, group in enumerate(groups):
        if group["name"].lower() == group_name.lower():
            groups[i]["cities"] = cities
            groups[i]["email"] = group_email
            await message.answer(f"✅ `{group_name}` grubu güncellendi.")
            return
    
    # Add new group
    groups.append({
        "name": group_name,
        "cities": cities,
        "email": group_email
    })
    await message.answer(f"✅ `{group_name}` grubu eklendi.")

@router.message(Command("grsil"))
async def cmd_grsil(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Kullanım: /grsil <sıra_no>")
        return
        
    try:
        index = int(parts[1]) - 1
        if index < 0 or index >= len(groups):
            await message.answer("❌ Geçersiz sıra numarası.")
            return
            
        removed_group = groups.pop(index)
        await message.answer(f"✅ `{removed_group['name']}` grubu silindi.")
    except ValueError:
        await message.answer("❌ Geçersiz sıra numarası.")

@router.message(Command("gruplari_yenile"))
async def cmd_refresh_groups(message: Message):
    """Grupları .env'den yeniden yükler"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    try:
        from config import groups
        load_dotenv()
        GROUPS_CONFIG = os.getenv("GROUPS_CONFIG", "[]")
        groups.clear()
        groups.extend(json.loads(GROUPS_CONFIG))
        
        await message.answer(f"✅ Gruplar yenilendi. Toplam {len(groups)} grup yüklendi.")
    except Exception as e:
        await message.answer(f"❌ Grup yenileme hatası: {str(e)}")

@router.message(Command("grup_ornek"))
async def cmd_group_example(message: Message):
    """Grup JSON örneği gösterir"""
    example = """
Örnek Grup JSON:
[
  {
    "name": "ege",
    "cities": ["İzmir", "Aydın", "Muğla"],
    "email": "ege@example.com"
  },
  {
    "name": "akdeniz", 
    "cities": ["Antalya", "Mersin", "Adana"],
    "email": "akdeniz@example.com"
  }
]

.env dosyasına ekleyin:
GROUPS_CONFIG=[{"name": "ege", "cities": ["İzmir", "Aydın", "Muğla"], "email": "ege@example.com"}]
"""
    await message.answer(f"<pre>{example}</pre>", parse_mode="HTML")

@router.message(Command("proc"))
async def cmd_proc(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    processing_msg = await message.answer("⏳ Excel dosyaları işleniyor...")
    
    try:
        # Check for new emails
        new_files = await email_utils.check_email()
        if new_files:
            await message.answer(f"📥 {len(new_files)} yeni Excel dosyası bulundu.")
        
        # Process Excel files
        group_results = await excel_processor.process_excel_files()
        
        if not group_results:
            await processing_msg.edit_text("❌ İşlenecek veri bulunamadı.")
            return
        
        # Create and send group Excel files
        sent_groups = []
        for group_name, filepaths in group_results.items():
            # Find group email
            group_email = None
            for group in groups:
                if group["name"] == group_name:
                    group_email = group["email"]
                    break
            
            if not group_email:
                continue
                
            # Create group Excel
            group_filepath = await excel_processor.create_group_excel(group_name, filepaths)
            if group_filepath:
                # Send email with attachment
                now = datetime.datetime.now()
                subject = f"{group_name} Grubu Verileri - {now.strftime('%d/%m/%Y %H:%M')}"
                body = f"{group_name} grubu için Excel dosyası ekte gönderilmiştir."
                
                success = await email_utils.send_email(group_email, subject, body, group_filepath)
                if success:
                    sent_groups.append(group_name)
        
        # Send report
        if sent_groups:
            response = "✅ **Mail gönderildi:**\n\n"
            for i, group_name in enumerate(sent_groups, 1):
                response += f"{i}. {group_name}\n"
            await processing_msg.edit_text(response)
        else:
            await processing_msg.edit_text("❌ Hiçbir gruba mail gönderilemedi.")
            
    except Exception as e:
        logger.error(f"Proc command error: {e}")
        await processing_msg.edit_text(f"❌ İşlem sırasında hata oluştu: {str(e)}")

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Bot istatistiklerini gösterir"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    try:
        # Temp klasörü boyutu
        temp_size = 0
        for path, dirs, files in os.walk(file_utils.TEMP_DIR):
            for f in files:
                fp = os.path.join(path, f)
                temp_size += os.path.getsize(fp)
        temp_size_mb = temp_size / (1024 * 1024)
        
        stats_message = (
            "📊 **Bot İstatistikleri**\n\n"
            f"📧 **Kaynak Mailler:** {len(source_emails)}\n"
            f"👥 **Aktif Gruplar:** {len(groups)}\n"
            f"📁 **Temp Klasör Boyutu:** {temp_size_mb:.2f} MB\n"
            f"⏰ **Bot Çalışma Süresi:** {int(time.time() - BOT_START_TIME)} saniye\n"
            f"🤖 **Admin Sayısı:** {len(ADMIN_IDS)}"
        )
        
        await message.answer(stats_message)
        
    except Exception as e:
        await message.answer(f"❌ İstatistikler alınamadı: {str(e)}")

# Handler loader compatibility
async def register_handlers(router_instance: Router):
    """Register handlers with the router - required for handler_loader"""
    router_instance.include_router(router)
