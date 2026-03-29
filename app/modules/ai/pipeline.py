from pathlib import Path
import pickle
import numpy as np
from datetime import datetime
from .predictor import SolarFlarePredictor

# Global predictor (bir kez başlatılır)
predictor = SolarFlarePredictor()


def send_notifications(high_risk_count: int, avg_probability: float):
    """
    Yüksek risk durumunda tüm kullanıcılara bildirim gönderir.
    
    Args:
        high_risk_count: Yüksek risk olarak sınıflandırılan örnek sayısı
        avg_probability: Ortalama tahmini olasılık
    """
    try:
        from app.extensions import db_manager
        from app.modules.notification.service import send_email_notification
        
        # Tüm kullanıcıları al
        collection = db_manager.get_collection('users')
        all_users = list(collection.find())
        emails = [u.get('email') for u in all_users if u.get('email')]
        
        if not emails:
            print("   ℹ️ Bildirim gönderilecek kullanıcı tidak bulundu.")
            return
        
        # Bildirim içeriğini hazırla
        activity_level = int(avg_probability * 100)
        subject = f"⚠️ KRİTİK: Güneş Aktivitesi Yüksek Risk Tespit Edildi! %{activity_level}"
        content = f"""
Güneş aktivite seviyesi kritik eşiğe ulaştı!

📊 Bildirim Detayları:
- Aktivite Seviyesi: %{activity_level}
- Yüksek Risk Örnek Sayısı: {high_risk_count}
- Tarama Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🚨 UYARI: Güneş fırtınası meydana gelebilir. 
Kritik sistemleri kontrol edin ve gerekli önlemleri alın!

Beacon of Helios Sistem
        """
        
        # Tüm kullanıcılara mail gönder
        success_count = 0
        for email in emails:
            try:
                if send_email_notification(email, subject, content, activity_level):
                    success_count += 1
            except Exception as e:
                print(f"   ❌ {email}'e mail gönderilemedi: {e}")
        
        print(f"   ✅ {success_count}/{len(emails)} kullanıcıya bildirim gönderildi")
        
    except Exception as e:
        print(f"   ❌ Bildirim sistemi hatası: {e}")


def predict_flare(refresh_data=False):
    """
    Güneş flaklı tahmin yapıyor.
    
    Args:
        refresh_data (bool): True ise yeni veriler çeker ve temizler, 
                            False ise mevcut temiz veriyi kullanır.
    
    Returns:
        Tahmin sonuçları ve HTTP status kodu
    """
    try:
        current_dir = Path(__file__).resolve().parent.parent / "data" / "clean_data"
        X_3d_path = current_dir / "X_3d_harpnum_samples.pkl"
        
        if refresh_data or not X_3d_path.exists():
            print("🔄 Yeni veriler çekiliyor ve temizleniyor...")
            from app.modules.data.fetch_data.main import SharpDataPipeline
            from app.modules.data.clean_data.pipeline import CleanDataPipeline
            
            fetch_pipeline = SharpDataPipeline()
            fetch_pipeline.run()
            
            clean_pipeline = CleanDataPipeline()
            X_3d, df_hourly, harpnum_list = clean_pipeline.step()
        else:
            print("✅ Mevcut temiz veriler kullanılıyor...")
            with open(X_3d_path, "rb") as f:
                X_3d = pickle.load(f)
        
        # Tahmin yap
        predictions = predictor.predict(X_3d)
        
        return {
            "status": "success",
            "predictions": predictions if isinstance(predictions, list) else predictions.tolist(),
            "message": "Tahmin başarıyla tamamlandı"
        }, 200
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Tahmin sırasında hata oluştu"
        }, 500


def scheduled_predict_flare():
    """
    APScheduler tarafından her saat başında otomatik olarak çağrılır.
    Tahminleri kaydeder ve gerekli işlemleri yapar.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"⏰ SAATLİK TAHMİN BAŞLANDI: {timestamp}")
    print(f"{'='*60}")
    
    try:
        # Tahmin yap (yeni veriler çek)
        result, status_code = predict_flare(refresh_data=True)
        
        if result.get("status") == "success":
            predictions = result.get("predictions", [])
            
            # Tahmin sonuçlarını analiz et
            if isinstance(predictions, list) and len(predictions) > 0:
                # Her sample'ın olasılığını kontrol et
                high_risk_count = 0
                total_prob = 0
                
                for p in predictions:
                    if isinstance(p, dict):
                        prob = p.get("flare_probability", 0)
                        total_prob += prob
                        if prob >= 0.7:
                            high_risk_count += 1
                
                avg_probability = total_prob / len(predictions) if predictions else 0
            else:
                high_risk_count = 0
                avg_probability = 0
            
            print(f"✅ Tahmin BAŞARILI")
            print(f"   📊 Toplam örnek: {len(predictions)}")
            print(f"   🔴 Yüksek risk (%70+): {high_risk_count}")
            print(f"   📈 Ortalama olasılık: %{avg_probability*100:.2f}")
            
            # Eğer yüksek risk varsa bildirim gönder
            if high_risk_count > 0:
                try:
                    print(f"   🚨 Yüksek risk algılandı! Bildirim gönderiliyor...")
                    send_notifications(high_risk_count, avg_probability)
                except Exception as e:
                    print(f"   ⚠️ Bildirim gönderilemedi: {e}")
        else:
            print(f"❌ Tahmin BAŞARISIZ: {result.get('error', 'Bilinmiyor')}")
    
    except Exception as e:
        print(f"❌ Saatlik tahmin sırasında kritik hata: {e}")
    
    print(f"{'='*60}\n")