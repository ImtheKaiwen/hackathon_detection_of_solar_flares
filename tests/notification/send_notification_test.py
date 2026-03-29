import requests
import os
from dotenv import load_dotenv


load_dotenv()
def test_send_email_notification():
    """
    test
    """
    # Flask sunucunun adresi
    url = "http://127.0.0.1:5000/notify/alert"
    
    # .env'deki gizli anahtarımızı başlığa (Header) ekliyoruz
    headers = {
        "X-API-KEY": os.getenv("ALERT_API_KEY"),
        "Content-Type": "application/json"
    }

    
    # İstek gövdesi (opsiyonel, activity_level gönderilebilir)
    data = {
        "activity_level": 85
    }

    print("🛰️ Beacon of Helios uyarısı gönderiliyor...")
    print(f"API KEY: {os.getenv('ALERT_API_KEY')}")
    
    try:
        # Gerçek bir HTTP isteği atıyoruz
        response = requests.post(url, headers=headers, json=data)
        print(f"📊 Durum Kodu: {response.status_code}")
        print(f"📋 Cevap: {response.text}")
        
        # Sonuç kontrolü (Assert)
        if response.status_code == 200:
            print("✅ TEST BAŞARILI: Mailler kuyruğa alındı.")
            assert response.json()['status'] == True
        else:
            print(f"❌ TEST BAŞARISIZ: Durum kodu {response.status_code}")
            
    except Exception as e:
        print(f"📡 Sunucu kapalı! Önce Flask'ı çalıştır. Hata: {e}")

if __name__ == "__main__":
    test_send_email_notification()

