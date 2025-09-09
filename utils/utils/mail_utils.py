#utils/mail_utils.py
import smtplib
import os
from email.message import EmailMessage

# SMTP Ayarları (Gmail örneği)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = os.environ.get("SMTP_USER")  # Gmail adresi
SMTP_PASS = os.environ.get("SMTP_PASS")  # Gmail App Password

def send_excel_email(to_email: str, file_path: str, subject: str = None, body: str = None):
    """
    Excel dosyasını belirtilen e-posta adresine gönderir.
    """
    if subject is None:
        subject = f"Excel Dosyası: {os.path.basename(file_path)}"
    if body is None:
        body = f"Lütfen ekteki Excel dosyasını inceleyiniz: {os.path.basename(file_path)}"

    # Mesaj oluştur
    msg = EmailMessage()
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)

    # Dosya ekle
    with open(file_path, 'rb') as f:
        file_data = f.read()
        file_name = os.path.basename(file_path)
        msg.add_attachment(file_data, maintype='application', subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=file_name)

    # SMTP ile gönder
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
        print(f"[INFO] {file_name} başarıyla {to_email} adresine gönderildi.")
    except Exception as e:
        print(f"[ERROR] {file_name} gönderilemedi! Hata: {e}")
