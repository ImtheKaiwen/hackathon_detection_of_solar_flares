import requests
import os
from dotenv import load_dotenv

# .env dosyasını oku (API Key için)
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

    print("🛰️ Beacon of Helios uyarısı gönderiliyor...")
    
    try:
        # Gerçek bir HTTP isteği atıyoruz
        response = requests.post(url, headers=headers)
        
        # Sonuç kontrolü (Assert)
        if response.status_code == 200:
            print("✅ TEST BAŞARILI: Mailler kuyruğa alındı.")
            assert response.json()['status'] == True
        else:
            print(f"❌ TEST BAŞARISIZ: Durum kodu {response.status_code}")
            assert False
            
    except Exception as e:
        print(f"📡 Sunucu kapalı! Önce Flask'ı çalıştır. Hata: {e}")
        assert False

if __name__ == "__main__":
    test_send_email_notification()