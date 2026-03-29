from flask import Flask
from app.core import Config
from app.extensions import db_manager
from flask_cors import CORS
from app.modules.main import main_bp
from app.modules.user import user_bp
from app.modules.notification import notification_bp
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

def create_app() -> Flask:

    app = Flask(__name__)
    CORS(app=app, allow_headers="*")

    app.config.from_object(Config)
    print(Config.DB_NAME, Config.MONGO_URI, flush=True)
    db_manager.init_database(app.config['MONGO_URI'],app.config['DB_NAME'])

    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(notification_bp)
    
    # APScheduler konfigürasyonu
    scheduler = BackgroundScheduler()
    
    # Her saat başında tahmin yap
    @app.before_request
    def init_scheduler():
        if not scheduler.running:
            from app.modules.ai.pipeline import scheduled_predict_flare
            
            scheduler.add_job(
                func=scheduled_predict_flare,
                trigger="cron",
                hour="*",
                minute="0",
                second="0",
                id="hourly_flare_prediction",
                name="Hourly Solar Flare Prediction",
                replace_existing=True
            )
            scheduler.start()
            print("⏰ Saatlik tahmin scheduler başlatıldı!")
    
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        if scheduler.running:
            scheduler.shutdown()
    
    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    
    return app

    