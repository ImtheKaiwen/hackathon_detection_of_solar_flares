import smtplib
import os
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.extensions import db_manager

def send_email_notification(to_email: str, subject: str, content: str, activity_level: int) -> bool:
    msg = MIMEMultipart()
    msg['From'] = os.getenv("SMTP_USERNAME")
    msg['To'] = to_email
    msg['Subject'] = subject

    # 🔥 Dinamik CSS Sınıfı
    card_class = "warning" # Varsayılan %70+ (Kırmızı)
    if activity_level >= 80: 
        card_class = "danger" # %80+ (Koyu Kırmızı)

    # Süslü parantez çakışmasını önlemek için CSS ayrı bir string olarak tanımlanıyor
    css_style = """
    <style>
        body, html {
            margin: 0; padding: 0; width: 100%; height: 100%;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #050510;
            background-image: url('https://i.imgur.com/962LmyP.png');
            background-size: cover; background-position: center; background-attachment: fixed;
            color: white; display: flex; align-items: center; justify-content: center;
        }
        .container {
            display: flex; width: 90%; max-width: 1200px; min-height: 80vh;
            background: rgba(10, 15, 25, 0.4); backdrop-filter: blur(8px);
            border-radius: 20px; overflow: hidden; box-shadow: 0 0 40px rgba(0,0,0,0.9);
            border: 1px solid rgba(255,255,255,0.05); margin: 40px auto;
        }
        .left-panel, .right-panel {
            flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px;
        }
        .sun-logo {
            max-width: 90%; max-height: 90%; object-fit: contain; border-radius: 50%;
            filter: drop-shadow(0 0 30px rgba(251, 191, 36, 0.4)); 
        }
        .alert-card {
            width: 100%; max-width: 450px; background: rgba(13, 17, 29, 0.95);
            border-radius: 12px; overflow: hidden; box-shadow: 0 25px 50px rgba(0,0,0,0.8);
        }
        .alert-card.warning { border: 2px solid #ef4444; } 
        .alert-card.danger { border: 2px solid #991b1b; } 
        .card-header {
            background-color: #000; text-align: center; padding: 30px 20px; border-bottom: 3px solid #f59e0b;
        }
        .card-header .icon { font-size: 28px; margin-bottom: 10px; }
        .card-header h1 {
            color: #fff; letter-spacing: 4px; font-size: 22px; font-weight: 900; margin: 0; text-transform: uppercase;
        }
        .card-body { padding: 40px 30px; text-align: center; }
        .card-body h2 { color: #fbbf24; font-size: 19px; margin-top: 0; margin-bottom: 25px; letter-spacing: 1px; }
        .alert-box {
            background-color: rgba(255, 255, 255, 0.03); border-left: 4px solid #ef4444;
            padding: 20px; margin-bottom: 25px; text-align: left;
        }
        .danger .alert-box { border-left-color: #991b1b; }
        .warning .alert-box { border-left-color: #ef4444; }
        .alert-box p { font-family: 'Courier New', monospace; font-size: 15px; margin: 0; line-height: 1.6; color: #fca5a5; }
        .instruction { color: #94a3b8; font-size: 14px; margin-bottom: 30px; }
        .status-badge {
            display: inline-block; background-color: #ef4444; color: #fff;
            padding: 8px 16px; border-radius: 6px; font-size: 14px; font-weight: bold;
        }
        .danger .status-badge { background-color: #991b1b; }
        .warning .status-badge { background-color: #ef4444; }
        .card-footer { background-color: rgba(0,0,0,0.6); padding: 15px; text-align: center; font-size: 12px; color: #64748b; }
        @media (max-width: 900px) {
            .container { flex-direction: column; height: auto; margin: 20px; }
            .left-panel { padding: 30px 20px 10px 20px; }
            .sun-logo { max-width: 250px; }
            .right-panel { padding: 10px 20px 30px 20px; }
        }
    </style>
    """

    # ✨ YENİ TASARIM
    html_template = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {css_style}
    </head>
    <body>
        <div class="container">
            <div class="left-panel">
                <img src="https://i.imgur.com/RosS0b0.jpeg" alt="Helios Sun Logo" class="sun-logo">
            </div>
            <div class="right-panel">
                <div class="alert-card {card_class}"> 
                    <div class="card-header">
                        <div class="icon">🛰️</div>
                        <h1>BEACON OF HELIOS</h1>
                    </div>
                    <div class="card-body">
                        <h2>🚨 KRİTİK GÜNEŞ AKTİVİTESİ</h2>
                        <div class="alert-box">
                            <p>{content}</p>
                        </div>
                        <p class="instruction">Lütfen ROV ve diğer elektronik sistemleri güvenlik moduna alınız.</p>
                        <div class="status-badge">
                            Aktivite Seviyesi: %{activity_level}
                        </div>
                    </div>
                    <div class="card-footer">
                        © 2026 Beacon of Helios | Erken Uyarı Sistemi
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_template, 'html'))
    status = "failed"
    try:
        server = smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT")))
        server.starttls()
        server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))
        server.send_message(msg)
        server.quit()
        status = "success"
        return True
    except Exception as e:
        print(f"SMTP Hatası: {e}")
        return False
    finally:
        try:
            log_col = db_manager.get_collection('notifications')
            log_col.insert_one({
                "recipient": to_email,
                "sent_at": datetime.datetime.now(),
                "delivery_status": status,
                "activity_level": activity_level
            })
        except: pass