#handlers/email_handlers.py
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

# process komutunu güncelleyin:
# handlers/email_handlers.py - process komutunu düzeltelim
# handlers/email_handlers.py - process komutunu güncelleyelim
# handlers/email_handlers.py - process komutuna debug ekleyelim
@router.message(Command("process"))
async def cmd_process(message: Message):
    """Excel dosyalarını işleme komutu"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    processing_msg = await message.answer("⏳ Excel dosyaları işleniyor...")
    
    try:
        # Process Excel files
        logger.info("🔄 process_excel_files() çağrılıyor...")
        group_results = await process_excel_files()
        logger.info(f"✅ process_excel_files() sonuç: {group_results}")
        
        if not group_results:
            await processing_msg.edit_text("❌ İşlenecek veri bulunamadı.")
            return
        
        # Create and send group Excel files
        sent_groups = []
        failed_groups = []
        
        for group_no, filepaths in group_results.items():
            logger.info(f"🔄 Processing group {group_no} with {len(filepaths)} files")
            
            # Find group email
            group_info = next((g for g in groups if g["no"] == group_no), None)
            if not group_info or not group_info.get("email"):
                failed_msg = f"{group_no} (email yok)"
                logger.warning(failed_msg)
                failed_groups.append(failed_msg)
                continue
                
            # Create group Excel
            logger.info(f"🔄 create_group_excel çağrılıyor...")
            group_filepath = await create_group_excel(group_no, filepaths)
            
            if not group_filepath:
                failed_msg = f"{group_no} (Excel oluşturulamadı)"
                logger.error(failed_msg)
                failed_groups.append(failed_msg)
                continue
            
            # ... email gönderme kodu 
            
            # Send email with attachment
            now = datetime.datetime.now()
            subject = f"{group_no} - {group_name} Grubu Verileri - {now.strftime('%d/%m/%Y %H:%M')}"
            body = f"{group_name} grubu için Excel dosyası ekte gönderilmiştir.\n\nToplam {len(filepaths)} dosya işlenmiştir."
            
            success = await send_email(group_email, subject, body, group_filepath)
            if success:
                sent_groups.append(f"{group_no} - {group_name}")
            else:
                failed_groups.append(f"{group_no} (mail gönderilemedi)")
        
        # Send report
        response = ""
        if sent_groups:
            response += "✅ **Mail gönderildi:**\n"
            for i, group_info in enumerate(sent_groups, 1):
                response += f"{i}. {group_info}\n"
            response += "\n"
        
        if failed_groups:
            response += "❌ **Hatalı gruplar:**\n"
            for i, group_info in enumerate(failed_groups, 1):
                response += f"{i}. {group_info}\n"
        
        if not sent_groups and not failed_groups:
            response = "⚠️ **Hiçbir işlem yapılamadı**"
        
        await processing_msg.edit_text(response)
            
    except Exception as e:
        logger.error(f"Process command error: {e}", exc_info=True)
        await processing_msg.edit_text(f"❌ İşlem sırasında hata oluştu: {str(e)}")
        

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
