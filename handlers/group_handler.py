"""
Grup Yönetimi için Yeni Handler (handlers/group_handler.py
"""
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
import logging
from config import groups, save_groups, ADMIN_IDS
import json

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("gruplar"))
async def cmd_gruplar(message: Message):
    """Tüm grupları listeler"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    if not groups:
        await message.answer("❌ Hiç grup bulunamadı.")
        return
        
    response = "👥 **Tüm Gruplar:**\n\n"
    for i, grup in enumerate(groups, 1):
        response += f"{i}. **{grup['no']} - {grup['ad']}**\n"
        response += f"   📍 İller: {grup['iller']}\n"
        response += f"   📧 Email: `{grup['email']}`\n\n"
        
    await message.answer(response)

@router.message(Command("grupekle"))
async def cmd_grupekle(message: Message):
    """Yeni grup ekler"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.answer("Kullanım: /grupekle <grup_no> <grup_ad> <iller> <email>")
        await message.answer("Örnek: /grupekle GRUP_15 MARMARA İstanbul,Kocaeli,Sakarya marmara@example.com")
        return
        
    grup_no = parts[1]
    grup_ad = parts[2]
    iller = parts[3]
    email = parts[4] if len(parts) > 4 else ""
    
    # Email kontrolü
    if not email or "@" not in email:
        await message.answer("❌ Geçerli bir email adresi giriniz.")
        return
    
    # Grup numarası kontrolü
    for grup in groups:
        if grup["no"] == grup_no:
            await message.answer(f"❌ {grup_no} numaralı grup zaten mevcut.")
            return
    
    # Yeni grup ekle
    yeni_grup = {
        "no": grup_no,
        "ad": grup_ad,
        "iller": iller,
        "email": email
    }
    
    groups.append(yeni_grup)
    save_groups(groups)
    
    await message.answer(f"✅ **{grup_no} - {grup_ad}** grubu başarıyla eklendi.")

@router.message(Command("grupsil"))
async def cmd_grupsil(message: Message):
    """Grup siler"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Kullanım: /grupsil <grup_no>")
        return
        
    grup_no = parts[1]
    
    # Grubu bul ve sil
    for i, grup in enumerate(groups):
        if grup["no"] == grup_no:
            silinen_grup = groups.pop(i)
            save_groups(groups)
            await message.answer(f"✅ **{silinen_grup['no']} - {silinen_grup['ad']}** grubu silindi.")
            return
    
    await message.answer(f"❌ {grup_no} numaralı grup bulunamadı.")

@router.message(Command("grupduzenle"))
async def cmd_grupduzenle(message: Message):
    """Grup düzenler"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    parts = message.text.split(maxsplit=4)
    if len(parts) < 5:
        await message.answer("Kullanım: /grupduzenle <grup_no> <yeni_ad> <yeni_iller> <yeni_email>")
        await message.answer("Örnek: /grupduzenle GRUP_1 YENI_AD İzmir,Aydin yeni@email.com")
        return
        
    grup_no = parts[1]
    yeni_ad = parts[2]
    yeni_iller = parts[3]
    yeni_email = parts[4]
    
    # Grubu bul ve düzenle
    for grup in groups:
        if grup["no"] == grup_no:
            grup["ad"] = yeni_ad
            grup["iller"] = yeni_iller
            grup["email"] = yeni_email
            save_groups(groups)
            await message.answer(f"✅ **{grup_no}** grubu güncellendi.")
            return
    
    await message.answer(f"❌ {grup_no} numaralı grup bulunamadı.")

@router.message(Command("grupyedekle"))
async def cmd_grupyedekle(message: Message):
    """Grupları JSON formatında yedekler"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    try:
        gruplar_json = json.dumps(groups, ensure_ascii=False, indent=2)
        await message.answer(f"<pre>{gruplar_json}</pre>", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Yedek oluşturulamadı: {str(e)}")

@router.message(Command("grupsifirla"))
async def cmd_grupsifirla(message: Message):
    """Grupları varsayılana sıfırlar"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu botu kullanma yetkiniz yok.")
        return
        
    from config import DEFAULT_GROUPS, save_groups
    groups.clear()
    groups.extend(DEFAULT_GROUPS)
    save_groups(groups)
    
    await message.answer("✅ Gruplar varsayılan ayarlara sıfırlandı.")

# Handler loader compatibility
async def register_handlers(router_instance: Router):
    """Register handlers with the router - required for handler_loader"""
    router_instance.include_router(router)
