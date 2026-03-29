from app import create_app
import os

if __name__ == "__main__":
    app = create_app()
    
    # Host 0.0.0.0 - tüm ağ arabirimlerine bağlan (container dışından erişim için zorunlu)
    # Port 5000 - Flask varsayılan portu
    # Debug mode - sadece development'da
    debug = os.getenv("FLASK_ENV") != "production"
    
    app.run(host="0.0.0.0", port=5000, debug=debug)