from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
import logging
from config import ADMIN_IDS
from utils.email_utils import check_email
from utils.excel_processor import process_excel_files, create_group_excel
from utils.file_utils import cleanup_temp
from utils.email_utils import send_email
from config import groups
import datetime

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("checkmail"))
async def cmd_checkmail(message: Message):
    """Manuel olarak mail kontrolü yapar"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    await message.answer("Mail kontrol ediliyor...")
    
    new_files = await check_email()
    if new_files:
        await message.answer(f"{len(new_files)} yeni Excel dosyası bulundu.")
    else:
        await message.answer("Yeni mail bulunamadı.")

@router.message(Command("process"))
async def cmd_process(message: Message):
    """Excel dosyalarını işleme komutu"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    await message.answer("Excel dosyaları işleniyor...")
    
    # Process Excel files
    group_results = await process_excel_files()
    
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
        group_filepath = await create_group_excel(group_name, filepaths)
        if group_filepath:
            # Send email with attachment
            now = datetime.datetime.now()
            subject = f"{group_name} Grubu Verileri - {now.strftime('%d/%m/%Y %H:%M')}"
            body = f"{group_name} grubu için Excel dosyası ekte gönderilmiştir."
            
            success = await send_email(group_email, subject, body, group_filepath)
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

@router.message(Command("cleanup"))
async def cmd_cleanup(message: Message):
    """Temp klasörünü temizleme komutu"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    await cleanup_temp()
    await message.answer("Temp klasörü temizlendi.")

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """İstatistikleri göster"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    import os
    from config import TEMP_DIR, source_emails, groups, processed_mail_ids
    
    temp_files = len([f for f in os.listdir(TEMP_DIR) if os.path.isfile(os.path.join(TEMP_DIR, f))])
    
    response = (
        f"📊 Bot İstatistikleri:\n\n"
        f"• Kaynak Mailler: {len(source_emails)}\n"
        f"• Gruplar: {len(groups)}\n"
        f"• İşlenmiş Mail ID'leri: {len(processed_mail_ids)}\n"
        f"• Temp Dosyaları: {temp_files}\n"
        f"• Admin ID'leri: {len(ADMIN_IDS)}"
    )
    
    await message.answer(response)

# Handler loader compatibility
async def register_handlers(router_instance: Router):
    """Register handlers with the router - required for handler_loader"""
    router_instance.include_router(router)
