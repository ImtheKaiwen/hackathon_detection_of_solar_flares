import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from app.extensions import db_manager

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_email_notification(to_email: str, subject: str, content: str) -> bool:
    msg = MIMEMultipart()
    msg['From'] = SMTP_USERNAME
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(content, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() 
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"E-posta gönderim hatası: {e}")
        return False

def alert():
    collection = db_manager.get_collection('user')
    if collection is None:
        return jsonify({'status': False, 'message': 'Veritabanı bağlantı hatası'}), 500
    
    all_users = collection.find()
    
    emails = [user.get('email') for user in all_users if user.get('email')]

    if not emails:
        return jsonify({'status': False, 'message': 'Sistemde e-posta gönderilecek kullanıcı bulunamadı.'}), 404

    success_count = 0
    for email in emails:
        try:
            response = send_email_notification(email, 'Sistem Uyarısı', 'Duyuru içeriği...')
            if response:
                success_count += 1
        except Exception as e:
            print(f"Hata: {email} adresine mail gönderilemedi. Sebep: {e}")

    return jsonify({
        'status': True, 
        'message': f'İşlem tamamlandı. {len(emails)} kişiden {success_count} kişiye bildirim başarıyla iletildi.'
    })