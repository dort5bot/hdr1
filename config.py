import os
from dotenv import load_dotenv

load_dotenv()

# Environment variables
TELEGRAM_BOT = os.getenv("TELEGRAM_BOT")
MAIL_K1 = os.getenv("MAIL_K1")
MAIL_K2 = os.getenv("MAIL_K2")
MAIL_K3 = os.getenv("MAIL_K3")
MAIL_K4 = os.getenv("MAIL_K4")
MAIL_BEN = os.getenv("MAIL_BEN")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

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
groups = []
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
