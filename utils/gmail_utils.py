#utils/gmail_utils.py
"""


"""
import imaplib
import email
import os

IMAP_SERVER = "imap.gmail.com"
EMAIL_USER = os.environ.get("SMTP_USER")  # Gmail adresi
EMAIL_PASS = os.environ.get("SMTP_PASS")  # App Password
SENDER_FILTER = "anadolugroupsigorta@gmail.com"  # Sadece bu adresten gelen

TEMP_DIR = os.path.join("data", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

def fetch_latest_excel():
    """
    Gmail inbox'u kontrol eder, belirlenen adresten gelen
    en son Excel dosyasını indirir ve yolunu döner.
    """
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")

    # Gönderen filtreli arama
    status, data = mail.search(None, f'(FROM "{SENDER_FILTER}")')
    mail_ids = data[0].split()

    if not mail_ids:
        return None

    latest_email_id = mail_ids[-1]  # en son mail

    status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    attachment_path = None

    for part in msg.walk():
        if part.get_content_maintype() == "application":
            filename = part.get_filename()
            if filename.endswith(".xlsx"):
                attachment_path = os.path.join(TEMP_DIR, filename)
                with open(attachment_path, "wb") as f:
                    f.write(part.get_payload(decode=True))
                break

    return attachment_path
