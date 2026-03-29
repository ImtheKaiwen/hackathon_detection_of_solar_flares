import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_email_notification(to_email: str, subject: str, content: str, activity_level: int = 70) -> bool:
    msg = MIMEMultipart()
    msg['From'] = os.getenv("SMTP_USERNAME")
    msg['To'] = to_email
    msg['Subject'] = subject

    html_template = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Beacon of Helios Alert</title>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            height: 100%;
            font-family: 'Arial', sans-serif;
            background: url('https://i.imgur.com/962LmyP.png') no-repeat center center fixed;
            background-size: cover;
            color: #ffffff;
            display: flex;
            justify-content: center;
            align-items: center;
        }}

        .container {{
            display: flex;
            flex-direction: row;
            width: 90%;
            max-width: 1000px;
            min-height: 400px;
            border-radius: 15px;
            overflow: hidden;
            background: url('https://imgur.com/a/4k7w1Kb') no-repeat center center fixed;
            background-size: cover;
        }}

        .left-panel {{
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 30px;
        }}

        .sun-logo {{
            max-width: 80%;
            border-radius: 50%;
        }}

        .right-panel {{
            flex: 1.2;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 30px;
        }}

        .alert-card {{
            width: 100%;
            padding: 20px 25px;
            border-radius: 8px;
        }}

        .alert-card h2 {{
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 18px;
            color: #ffffff;
            padding: 5px;
            border-radius: 8px;
            width: fit-content;
        }}

        .alert-box {{
            background-color: #0a1f3d;
            padding: 15px;
            font-size: 14px;
            color: #cbd5e1;
            border-radius: 4px;
            margin-bottom: 15px;
        }}

        .status-badge {{
            display: inline-block;
            padding: 6px 12px;
            background-color: #8a1e1e;
            color: #ffffff;
            border-radius: 4px;
            font-weight: bold;
            font-size: 13px;
        }}

        .card-footer {{
            text-align: center;
            margin-top: 15px;
            font-size: 12px;
            color: #94a3b8;
        }}

        @media (max-width: 900px) {{
            .container {{ flex-direction: column; }}
            .left-panel, .right-panel {{ padding: 20px; }}
        }}
    </style>
    </head>
    <body>
    <div class="container">
        <div class="left-panel">
            <img src="https://i.imgur.com/RosS0b0.jpeg" alt="Logo" class="sun-logo">
        </div>
        <div class="right-panel">
            <div class="alert-card warning">
                <h2>KRİTİK GÜNEŞ AKTİVİTESİ</h2>
                <div class="alert-box">
                    Güneş fırtınası algılandı. ROV ve diğer sistemleri güvenli moda alın.
                </div>
                <div class="status-badge">Aktivite Seviyesi: %{activity_level}</div>
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
