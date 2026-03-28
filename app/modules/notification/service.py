import smtplib
import os
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import jsonify
from app.extensions import db_manager

# .env dosyasından ayarları çekiyoruz
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_email_notification(to_email: str, subject: str, content: str) -> bool:
    """
    Kullanıcıya şık bir HTML mail gönderir ve sonucu veritabanına loglar.
    """
    msg = MIMEMultipart()
    msg['From'] = SMTP_USERNAME
    msg['To'] = to_email
    msg['Subject'] = subject

    # 1. GÖREV: HTML TASARIMI (Beacon of Helios Temalı)
    html_template = f"""
    <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #020617; color: #f8fafc; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: #0f172a; border: 2px solid #fbbf24; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                <div style="background: linear-gradient(90deg, #f59e0b, #d97706); padding: 20px; text-align: center;">
                    <h1 style="margin: 0; color: #ffffff; font-size: 24px; letter-spacing: 2px;">🛰️ BEACON OF HELIOS</h1>
                </div>
                <div style="padding: 30px;">
                    <h2 style="color: #fbbf24; border-bottom: 1px solid #1e293b; padding-bottom: 10px;">Güneş Aktivitesi Uyarısı</h2>
                    <p style="font-size: 16px; line-height: 1.6;">Sistemimiz tarafından tespit edilen kritik veri şudur:</p>
                    <div style="background: #1e293b; border-left: 4px solid #ef4444; padding: 20px; margin: 20px 0; font-style: italic; color: #f1f5f9;">
                        "{content}"
                    </div>
                    <p style="font-size: 14px; color: #94a3b8;">Lütfen ROV ve diğer elektronik sistemleri güvenlik moduna alınız.</p>
                </div>
                <div style="background: #1e293b; padding: 15px; text-align: center; font-size: 12px; color: #64748b;">
                    © 2026 Beacon of Helios | Erken Uyarı Sistemi
                </div>
            </div>
        </body>
    </html>
    """
    
    msg.attach(MIMEText(html_template, 'html'))

    status = "failed"
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() 
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        status = "success"
        return True
    except Exception as e:
        print(f"E-posta gönderim hatası ({to_email}): {e}")
        return False
    finally:
        # 2. GÖREV: ÖZEL VERİTABANI KAYDI (Loglama)
        try:
            log_collection = db_manager.get_collection('notifications')
            if log_collection is not None:
                log_collection.insert_one({
                    "recipient": to_email,
                    "subject": subject,
                    "content": content,
                    "sent_at": datetime.datetime.now(), # Tam olarak ne zaman gitti?
                    "delivery_status": status # Başarılı mı başarısız mı?
                })
        except Exception as db_err:
            print(f"Veritabanı loglama hatası: {db_err}")

def alert():
    """
    Tüm kullanıcılara toplu uyarı gönderir. API Key ile korunmalıdır.
    """
    # 3. GÖREV: GÜVENLİK (Key Gömme)
    from flask import request
    api_key = request.headers.get('X-API-KEY')
    if api_key != os.getenv("ALERT_API_KEY"):
        return jsonify({'status': False, 'message': 'Yetkisiz erişim! Geçersiz API Key.'}), 403

    collection = db_manager.get_collection('user')
    if collection is None:
        return jsonify({'status': False, 'message': 'Veritabanı bağlantı hatası'}), 500
    
    all_users = list(collection.find())
    emails = [user.get('email') for user in all_users if user.get('email')]

    if not emails:
        return jsonify({'status': False, 'message': 'Sistemde e-posta gönderilecek kullanıcı bulunamadı.'}), 404

    success_count = 0
    for email in emails:
        # Her kullanıcı için özel içerik (örneğin %70 olasılık bilgisi)
        response = send_email_notification(email, 'KRİTİK: Güneş Patlaması Aktivitesi', 'Güneş patlaması olasılığı %60\'ın üzerine çıkmıştır. Sistemler risk altında!')
        if response:
            success_count += 1

    return jsonify({
        'status': True, 
        'message': f'İşlem tamamlandı. {len(emails)} kişiden {success_count} kişiye bildirim başarıyla iletildi.'
    })