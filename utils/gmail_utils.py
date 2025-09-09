import imaplib
import email
import os
import json

IMAP_SERVER = "imap.gmail.com"
EMAIL_USER = os.environ.get("SMTP_USER")
EMAIL_PASS = os.environ.get("SMTP_PASS")
SENDER_FILTER = os.environ.get("SENDER_FILTER", "anadolugroupsigorta@gmail.com")  # .env ile ayarlanabilir

TEMP_DIR = os.path.join("data", "temp")
PROCESSED_FILE = os.path.join("data", "processed_ids.json")
os.makedirs(TEMP_DIR, exist_ok=True)

# İşlenmiş mail ID’lerini yükle
if os.path.exists(PROCESSED_FILE):
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        PROCESSED_IDS = set(json.load(f))
else:
    PROCESSED_IDS = set()


def save_processed_ids():
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(list(PROCESSED_IDS), f)


def fetch_all_new_excels():
    """
    Gmail inbox'u kontrol eder.
    İşlenmemiş tüm maillerdeki Excel dosyalarını indirir.
    Geriye: [dosya_yolu1, dosya_yolu2, ...]
    """
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")

    status, data = mail.search(None, f'(FROM "{SENDER_FILTER}")')
    mail_ids = data[0].split()
    new_files = []

    for mail_id in mail_ids:
        mail_id_str = mail_id.decode()
        if mail_id_str in PROCESSED_IDS:
            continue  # daha önce işlenmiş

        status, msg_data = mail.fetch(mail_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        for part in msg.walk():
            if part.get_content_maintype() == "application" and part.get_filename() and part.get_filename().endswith(".xlsx"):
                filename = part.get_filename()
                filepath = os.path.join(TEMP_DIR, filename)
                # Eğer aynı isimli dosya varsa uniq yap
                counter = 1
                base, ext = os.path.splitext(filename)
                while os.path.exists(filepath):
                    filepath = os.path.join(TEMP_DIR, f"{base}_{counter}{ext}")
                    counter += 1

                with open(filepath, "wb") as f:
                    f.write(part.get_payload(decode=True))
                new_files.append(filepath)

        # Mail işlenmiş olarak kaydet
        PROCESSED_IDS.add(mail_id_str)

    save_processed_ids()
    return new_files
