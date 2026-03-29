# ai/predictor.py
import os
import torch
import joblib
import numpy as np
from .model import SolarFlarePredictorModel

class SolarFlarePredictor:
    """
    Modeli belleğe yükler ve tahmin işlemlerini yönetir.
    Singleton gibi çalışması için Flask ayağa kalkarken 1 kez başlatılır.
    """
    def __init__(self):
        # Yolları belirle (Bulunduğumuz klasöre göre göreceli)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(base_dir, 'weights', 'solar_flare_lstm_attention_best.pth')
        self.scaler_path = os.path.join(base_dir, 'weights', 'solar_flare_scaler.pkl')
        
        # Model Hiperparametreleri (Eğitimdeki ile BİREBİR aynı olmalı!)
        self.input_dim = 24  
        self.hidden_dim = 64
        self.num_layers = 2
        
        # Cihaz ayarı (CPU veya GPU)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 1. Scaler'ı Yükle
        if not os.path.exists(self.scaler_path):
            raise FileNotFoundError(f"Scaler bulunamadı: {self.scaler_path}")
        self.scaler = joblib.load(self.scaler_path)
        
        # 2. Modeli Başlat ve Ağırlıkları Yükle
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model ağırlıkları bulunamadı: {self.model_path}")
            
        self.model = SolarFlarePredictorModel(
            input_dim=self.input_dim, 
            hidden_dim=self.hidden_dim, 
            num_layers=self.num_layers
        )
        self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval() # Dropouth vs. kapat, test moduna al!
        
        print("✅ Solar Flare Predictor belleğe yüklendi ve hazır!")

    def preprocess(self, raw_data):
        """
        Gelen ham veriyi modele uygun hale getirir.
        raw_data boyutu: (zaman_adimi, 24) olmalıdır. (Örn: 60 saat, 24 feature)
        """
        # Verinin numpy array olduğundan emin ol
        data = np.array(raw_data)
        
        # Scaler ile dönüştür (Eğitimdeki gibi)
        # Not: Scaler genellikle 2D bekler. Eğer (Time_steps, Features) geliyorsa tam oturur.
        scaled_data = self.scaler.transform(data)
        
        # PyTorch modelimiz (Batch, Time_steps, Features) bekler. 
        # Tek bir tahmin yapacağımız için başa Batch boyutu (1) ekliyoruz.
        # (1, 60, 24)
        tensor_data = torch.tensor(scaled_data, dtype=torch.float32).unsqueeze(0)
        return tensor_data.to(self.device)

    def predict(self, raw_data):
        """
        Tahmin yapar. 
        raw_data şekli:
        - Tek örnek: (60, 24) - 60 saatlik veri, 24 feature
        - Batch: (num_samples, 60, 24)
        
        Returns:
        - Tek örnek için: dict {"success": bool, "flare_probability": float, ...}
        - Batch için: list of dicts
        """
        try:
            data = np.array(raw_data)
            
            # Batch olup olmadığı kontrol et
            if data.ndim == 2:
                # Tek örnek (60, 24)
                return self._predict_single(data)
            elif data.ndim == 3:
                # Batch (num_samples, 60, 24)
                results = []
                for sample in data:
                    result = self._predict_single(sample)
                    results.append(result)
                return results
            else:
                raise ValueError(f"Beklenmedik veri şekli: {data.shape}")
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _predict_single(self, sample):
        """Tek bir örnek için tahmin yapar. sample şekli: (60, 24)"""
        try:
            # 1. Ön işlem
            input_tensor = self.preprocess(sample)
            
            # 2. Tahmin
            with torch.no_grad():
                olasilik, attn_weights = self.model(input_tensor)
                
            # 3. Sonuçları düzenle
            prob_value = olasilik.item()
            
            return {
                "success": True,
                "flare_probability": round(prob_value, 4),
                "will_flare": bool(prob_value >= 0.5)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }