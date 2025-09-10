from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
import logging
from config import source_emails, groups, ADMIN_IDS
from utils import email_utils, excel_processor, file_utils

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    await message.answer(
        "HIDIR Botuna Hoşgeldiniz!\n\n"
        "Kullanılabilir komutlar:\n"
        "/kay - Kaynak mail adreslerini listeler\n"
        "/kayek - Kaynak mail adresi ekler\n"
        "/kaysil - Kaynak mail adresi siler\n"
        "/gr - Grupları listeler\n"
        "/grek - Yeni grup ekler\n"
        "/grsil - Grup siler\n"
        "/checkmail - Manuel olarak mail kontrolü yapar\n"
        "/process - Sadece Excel işleme yapar (mail kontrolü yapmaz)\n"
        "/cleanup - Temp klasörünü manuel temizler\n"
        "/stats - Bot istatistiklerini gösterir\n"
        "/proc - Excel dosyalarını işler"
    )

@router.message(Command("kay"))
async def cmd_kay(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    if not source_emails:
        await message.answer("Kaynak mail adresi bulunamadı.")
        return
        
    response = "Kaynak Mail Adresleri:\n\n"
    for i, email in enumerate(source_emails, 1):
        response += f"{i}. {email}\n"
        
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
        await message.answer(f"{new_email} zaten kayıtlı.")
        return
        
    source_emails.append(new_email)
    await message.answer(f"{new_email} kaynak mail olarak eklendi.")

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
            await message.answer("Geçersiz sıra numarası.")
            return
            
        removed_email = source_emails.pop(index)
        await message.answer(f"{removed_email} kaynak mail olarak silindi.")
    except ValueError:
        await message.answer("Geçersiz sıra numarası.")

@router.message(Command("gr"))
async def cmd_gr(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    if not groups:
        await message.answer("Grup bulunamadı.")
        return
        
    response = "Gruplar:\n\n"
    for i, group in enumerate(groups, 1):
        cities = ", ".join(group["cities"])
        response += f"{i}. {group['name']} - {cities} - {group['email']}\n"
        
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
            await message.answer(f"{group_name} grubu güncellendi.")
            return
    
    # Add new group
    groups.append({
        "name": group_name,
        "cities": cities,
        "email": group_email
    })
    await message.answer(f"{group_name} grubu eklendi.")

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
            await message.answer("Geçersiz sıra numarası.")
            return
            
        removed_group = groups.pop(index)
        await message.answer(f"{removed_group['name']} grubu silindi.")
    except ValueError:
        await message.answer("Geçersiz sıra numarası.")

@router.message(Command("proc"))
async def cmd_proc(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    await message.answer("Excel dosyaları işleniyor...")
    
    # Check for new emails
    new_files = await email_utils.check_email()
    if new_files:
        await message.answer(f"{len(new_files)} yeni Excel dosyası bulundu.")
    
    # Process Excel files
    group_results = await excel_processor.process_excel_files()
    
    if not group_results:
        await message.answer("İşlenecek veri bulunamadı.")
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
        response = "Mail gönderildi:\n"
        for i, group_name in enumerate(sent_groups, 1):
            response += f"{i}. {group_name}\n"
        await message.answer(response)
    else:
        await message.answer("Hiçbir gruba mail gönderilemedi.")
