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

# TEMP_DIR tanımı (file_utils'den alıyoruz)
TEMP_DIR = file_utils.TEMP_DIR

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
        "/status - Detaylı durum\n\n"
        "🔧 **Debug Komutları:**\n"
        "/debug - Debug menüsü\n"
        "/files - Temp dosyalarını listele\n"
        "/testmail - Test maili gönder\n"
        "/testexcel - Excel işleme testi"
        "/normalize_test - Normalizasyon testi yap: \n"
        "/detayli_test - Detaylı test yap: \n"
        "/testexcel - Excel işlemeyi dene: \n"
    )

# handlers/commands.py'e yeni komutlar ekleyelim
@router.message(Command("detayli_test"))
async def cmd_detayli_test(message: Message):
    """Detaylı Excel testi yapar"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    try:
        # Tüm Excel dosyalarını tek tek test et
        excel_files = [f for f in os.listdir(TEMP_DIR) if f.lower().endswith(('.xlsx', '.xls'))]
        
        if not excel_files:
            await message.answer("❌ Test edilecek Excel dosyası yok.")
            return
        
        response = "🔍 **Detaylı Excel Testi:**\n\n"
        
        for filename in excel_files:
            filepath = os.path.join(TEMP_DIR, filename)
            df = pd.read_excel(filepath)
            
            response += f"📊 **{filename}**\n"
            response += f"   Sütunlar: {list(df.columns)}\n"
            
            # Şehir sütunu ara
            city_column = None
            for col in df.columns:
                col_normalized = normalize_text(col)
                if any(keyword in col_normalized for keyword in ['SEHIR', 'CITY', 'IL']):
                    city_column = col
                    break
            
            if city_column:
                response += f"   ✅ Şehir sütunu: {city_column}\n"
                
                # İlk 5 şehir değerini göster
                sehirler = []
                for i in range(min(5, len(df))):
                    city_val = df.iloc[i][city_column]
                    if pd.notna(city_val):
                        sehirler.append(str(city_val))
                response += f"   Örnek değerler: {sehirler}\n"
            else:
                response += f"   ❌ Şehir sütunu bulunamadı\n"
            
            response += "\n"
        
        await message.answer(response[:4000])
        
    except Exception as e:
        logger.error(f"Detaylı test hatası: {e}")
        await message.answer(f"❌ Detaylı test hatası: {str(e)}")

@router.message(Command("normalize_test"))
async def cmd_normalize_test(message: Message):
    """Büyük-küçük harf normalizasyon testi"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    try:
        # Test için örnek değerler
        test_values = ["AFYON", "Afyon", "afyon", "İSTANBUL", "istanbul", "Istanbul"]
        
        response = "🔠 **Normalizasyon Testi:**\n\n"
        
        for value in test_values:
            normalized = normalize_text(value)
            response += f"'{value}' -> '{normalized}'\n"
        
        # Grup illerinden örnekler
        response += "\n**Grup İlleri (Normalize):**\n"
        for group in groups[:3]:  # İlk 3 grup
            iller_normalized = [normalize_text(il) for il in group["iller"].split(",")]
            response += f"{group['no']}: {iller_normalized[:3]}...\n"
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Normalizasyon test hatası: {e}")
        await message.answer(f"❌ Normalizasyon test hatası: {str(e)}")
        
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

# handlers/commands.py - grupları gösteren komutu düzeltelim
@router.message(Command("gruplar", "gr"))
async def cmd_gruplar(message: Message):
    """Tüm grupları listeler (/gruplar ve /gr)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    if not groups:
        await message.answer("❌ Hiç grup bulunamadı.")
        return
        
    response = "👥 **Tüm Gruplar:**\n\n"
    for i, grup in enumerate(groups, 1):
        response += f"{i}. **{grup['no']} - {grup['name']}**\n"
        response += f"   📍 İller: {grup['iller']}\n"
        response += f"   📧 Email: `{grup['email']}`\n\n"
        
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

@router.message(Command("debug"))
async def cmd_debug(message: Message):
    """Debug ve test komutları"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    debug_info = """
🔧 **Debug Komutları:**
    
/files - Temp'deki dosyaları listeler
/testmail - Test maili gönderir
/testexcel - Excel işleme testi yapar
/logs - Son logları gösterir
"""
    await message.answer(debug_info)

@router.message(Command("files"))
async def cmd_files(message: Message):
    """Temp'deki dosyaları listeler"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    try:
        files = os.listdir(TEMP_DIR)
        if not files:
            await message.answer("❌ Temp klasörü boş.")
            return
            
        response = "📁 **Temp Dosyaları:**\n\n"
        for i, file in enumerate(files, 1):
            file_path = os.path.join(TEMP_DIR, file)
            size = os.path.getsize(file_path) / 1024  # KB cinsinden
            response += f"{i}. {file} ({size:.1f} KB)\n"
            
        await message.answer(response)
    except Exception as e:
        await message.answer(f"❌ Hata: {str(e)}")

@router.message(Command("testmail"))
async def cmd_testmail(message: Message):
    """Test maili gönderir"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    try:
        # İlk gruba test maili gönder
        if not groups:
            await message.answer("❌ Test için grup bulunamadı.")
            return
            
        test_group = groups[0]
        success = await email_utils.send_email(
            test_group["email"],
            "HIDIR Bot Test Maili",
            "Bu bir test mailidir. Bot çalışıyor!",
            None  # Ek dosya yok
        )
        
        if success:
            await message.answer(f"✅ Test maili gönderildi: {test_group['email']}")
        else:
            await message.answer("❌ Test maili gönderilemedi.")
            
    except Exception as e:
        await message.answer(f"❌ Test hatası: {str(e)}")

# handlers/commands.py - testexcel komutunu düzeltelim
@router.message(Command("testexcel"))
async def cmd_testexcel(message: Message):
    """Excel işleme testi yapar"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    try:
        # Excel işleme testi
        results = await excel_processor.process_excel_files()
        
        if not results:
            await message.answer("❌ İşlenecek Excel bulunamadı veya gruplandırma yapılamadı.")
            return
            
        response = "✅ **Excel İşleme Sonuçları:**\n\n"
        for group_no, files in results.items():
            # Grup bilgisini bul
            group_info = next((g for g in groups if g["no"] == group_no), None)
            group_name = group_info["name"] if group_info else "Bilinmeyen"
            group_email = group_info["email"] if group_info else "Bilinmeyen"
            
            response += f"📊 {group_no} - {group_name} ({group_email}): {len(files)} dosya\n"
            
            # Dosya isimlerini göster (ilk 3)
            for i, file_path in enumerate(files[:3]):
                file_name = os.path.basename(file_path)
                response += f"   {i+1}. {file_name}\n"
            if len(files) > 3:
                response += f"   ... ve {len(files)-3} dosya daha\n"
            response += "\n"
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Excel test hatası: {e}")
        await message.answer(f"❌ Excel test hatası: {str(e)}")

# Handler loader compatibility
async def register_handlers(router_instance: Router):
    """Register handlers with the router - required for handler_loader"""
    router_instance.include_router(router)
