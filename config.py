import os
import json
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Webhook/Polling seçimi
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "3000"))

# Environment variables
TELEGRAM_BOT = os.getenv("TELEGRAM_BOT")
MAIL_K1 = os.getenv("MAIL_K1")
MAIL_K2 = os.getenv("MAIL_K2")
MAIL_K3 = os.getenv("MAIL_K3")
MAIL_K4 = os.getenv("MAIL_K4")
MAIL_BEN = os.getenv("MAIL_BEN")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

# Grup veri dosyası
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
GROUPS_FILE = DATA_DIR / "groups.json"

# Varsayılan gruplar (TUTARLI YAPI - "name" kullanıyoruz)
DEFAULT_GROUPS = [
    {"no": "GRUP_1", "name": "ANTALYA", "iller": "Afyon,Aksaray,Ankara,Antalya,Burdur,Çankırı,Isparta,Karaman,Kayseri,Kırıkkale,Kırşehir,Konya,Uşak", "email": "dersdep@gmail.com"},
    {"no": "GRUP_2", "name": "MERSİN", "iller": "Adana,Adıyaman,Batman,Bingöl,Bitlis,Diyarbakır,Elazığ,Gaziantep,Hakkâri,Hatay,Kahramanmaraş,Kilis,Malatya,Mardin,Mersin,Muş,Osmaniye,Siirt,Şanlıurfa,Şırnak", "email": "dersdep@gmail.com"},
    {"no": "GRUP_3", "name": "İZMİR", "iller": "Afyon,Aydın,Burdur,Isparta,İzmir,ÇANAKKALE,Manisa,Muğla,Uşak", "email": "GRUP_3@gmail.com"},
    {"no": "GRUP_4", "name": "BURSA", "iller": "Balıkesir,Bursa,Çanakkale,Düzce,Kocaeli,Sakarya,Tekirdağ,Yalova", "email": "GRUP_4@gmail.com"},
    {"no": "GRUP_5", "name": "BALIKESİR", "iller": "BALIKESİR,ÇANAKKALE", "email": "GRUP_5@gmail.com"},
    {"no": "GRUP_6", "name": "KARADENİZ", "iller": "Artvin,Bayburt,Çankırı,Erzincan,Erzurum,Giresun,Gümüşhane,Ordu,Rize,Samsun,Sinop,Sivas,Tokat,Trabzon", "email": "GRUP_6@gmail.com"},
    {"no": "GRUP_7", "name": "ERZİNCAN", "iller": "Bingöl,Erzincan,Erzurum,Giresun,Gümüşhane,Kars,Ordu,Sivas,Şırnak,Tokat,Tunceli", "email": "GRUP_7@gmail.com"},
    {"no": "GRUP_8", "name": "ESKİŞEHİR", "iller": "Afyon,Ankara,Bilecik,Eskişehir,Uşak", "email": "GRUP_8@gmail.com"},
    {"no": "GRUP_9", "name": "KÜTAHYA", "iller": "Afyon,Ankara,Bilecik,Bozüyük,Bursa,Eskişehir,Kütahya,Uşak", "email": "GRUP_9@gmail.com"},
    {"no": "GRUP_10", "name": "ÇORUM", "iller": "Amasya,Ankara,Çankırı,Çorum,Kastamonu,Kayseri,Kırıkkale,Kırşehir,Samsun,Tokat,Yozgat", "email": "GRUP_10@gmail.com"},
    {"no": "GRUP_11", "name": "DENİZLİ", "iller": "Afyon,Aydın,Burdur,Denizli,Isparta,İzmir,Manisa,Muğla,Uşak", "email": "GRUP_11@gmail.com"},
    {"no": "GRUP_12", "name": "AKHİSAR", "iller": "MANİSA", "email": "GRUP_12@gmail.com"},
    {"no": "GRUP_13", "name": "DÜZCE", "iller": "Bolu,Düzce,Edirne,İstanbul,Karabük,Kırklareli,Kocaeli,Sakarya,Tekirdağ,Yalova,Zonguldak", "email": "GRUP_13@gmail.com"},
    {"no": "GRUP_14", "name": "TUNCAY", "iller": "Aksaray,Ankara,Kahramanmaraş,Kırıkkale,Kırşehir", "email": "GRUP_14@gmail.com"}
]

# Grupları yükle
def load_groups():
    if GROUPS_FILE.exists():
        try:
            with open(GROUPS_FILE, 'r', encoding='utf-8') as f:
                loaded_groups = json.load(f)
                # Eski yapıyı yeni yapıya dönüştür
                return convert_old_groups(loaded_groups)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Groups file error: {e}, loading default groups")
            return DEFAULT_GROUPS
    else:
        # Dosya yoksa, varsayılan grupları kaydet ve döndür
        save_groups(DEFAULT_GROUPS)
        return DEFAULT_GROUPS

def convert_old_groups(old_groups):
    """Eski grup yapısını yeniye dönüştür"""
    new_groups = []
    for group in old_groups:
        new_group = group.copy()
        # "ad" alanı varsa "name" olarak değiştir
        if "ad" in new_group and "name" not in new_group:
            new_group["name"] = new_group.pop("ad")
        new_groups.append(new_group)
    return new_groups

def save_groups(groups_data):
    # Önce eski yapıyı yeni yapıya dönüştür
    converted_groups = convert_old_groups(groups_data)
    with open(GROUPS_FILE, 'w', encoding='utf-8') as f:
        json.dump(converted_groups, f, ensure_ascii=False, indent=2)

# Turkish city list
TURKISH_CITIES = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Aksaray", "Amasya", "Ankara", 
    "Antalya", "Ardahan", "Artvin", "Aydın", "Balıkesir", "Bartın", "Batman", 
    "Bayburt", "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", 
    "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Düzce", "Edirne", "Elazığ", 
    "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", 
    "Hakkâri", "Hatay", "Iğdır", "Isparta", "İstanbul", "İzmir", "Kahramanmaraş", 
    "Karabük", "Karaman", "Kars", "Kastamonu", "Kayseri", "Kırıkkale", "Kırklareli", 
    "Kırşehir", "Kilis", "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", 
    "Mardin", "Mersin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Osmaniye", 
    "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas", "Şanlıurfa", "Şırnak", 
    "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Uşak", "Van", "Yalova", "Yozgard", 
    "Zonguldak"
]

# Data storage
source_emails = []
processed_mail_ids = set()

# Initialize data from environment
if MAIL_K1:
    source_emails.append(MAIL_K1)
if MAIL_K2:
    source_emails.append(MAIL_K2)
if MAIL_K3:
    source_emails.append(MAIL_K3)
if MAIL_K4:
    source_emails.append(MAIL_K4)

# Temp directory
TEMP_DIR = os.path.join(os.getcwd(), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# IMAP ve SMTP ayarları
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Grupları başlat
groups = load_groups()
print(f"Loaded {len(groups)} groups from {GROUPS_FILE}")
