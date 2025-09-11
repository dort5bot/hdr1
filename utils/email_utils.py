#utils/email_utils.py
import imaplib
import email
from email.header import decode_header
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import logging
import os
from config import source_emails, TEMP_DIR, processed_mail_ids

logger = logging.getLogger(__name__)

async def check_email() -> list:
    """Check for new emails with Excel attachments from monitored addresses"""
    new_files = []
    
    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(os.getenv("MAIL_BEN"), os.getenv("MAIL_PASSWORD"))
        mail.select("inbox")
        
        # Search for all unseen emails
        status, messages = mail.search(None, 'UNSEEN')
        if status != "OK":
            return new_files
            
        email_ids = messages[0].split()
        
        for email_id in email_ids:
            # Fetch the email
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            if status != "OK":
                continue
                
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Check if email is from a monitored source
                    from_email = msg["From"]
                    if not any(source in from_email for source in source_emails):
                        continue
                    
                    # Check if we've already processed this email
                    if email_id in processed_mail_ids:
                        continue
                    
                    # Process attachments
                    for part in msg.walk():
                        if part.get_content_maintype() == 'multipart':
                            continue
                        if part.get('Content-Disposition') is None:
                            continue
                            
                        filename = part.get_filename()
                        if filename and any(filename.endswith(ext) for ext in ['.xlsx', '.xls']):
                            # Decode filename
                            filename_bytes, encoding = decode_header(filename)[0]
                            if isinstance(filename_bytes, bytes):
                                filename = filename_bytes.decode(encoding or 'utf-8')
                            
                            # Save the attachment
                            filepath = os.path.join(TEMP_DIR, filename)
                            with open(filepath, 'wb') as f:
                                f.write(part.get_payload(decode=True))
                            
                            new_files.append((filepath, from_email))
                            processed_mail_ids.add(email_id)
                            logger.info(f"New Excel file saved: {filename}")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        logger.error(f"Error checking email: {e}")
    
    return new_files

async def send_email(to_email: str, subject: str, body: str, attachment_path: str = None) -> bool:
    """Send email with attachment using SMTP"""
    try:
        # Email message
        msg = MIMEMultipart()
        msg['From'] = os.getenv("MAIL_BEN")
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Email body
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Attachment
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)
        
        # SMTP settings
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        username = os.getenv("MAIL_BEN")
        password = os.getenv("MAIL_PASSWORD")
        
        # Send email
        async with aiosmtplib.SMTP(hostname=smtp_server, port=smtp_port) as smtp:
            await smtp.connect()
            await smtp.starttls()
            await smtp.login(username, password)
            await smtp.send_message(msg)
        
        logger.info(f"Email successfully sent to: {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Email sending error: {e}")
        return False
