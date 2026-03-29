import os
import time
from flask import Blueprint, request, jsonify,current_app
from app.modules.notification.service import send_email_notification
from app.extensions import db_manager
from app.extensions import socketio

notification_bp = Blueprint('notification', __name__, url_prefix='/notify')

@notification_bp.route('/alert', methods=['POST'])
def alert():
    api_key = request.headers.get('X-API-KEY')
    if api_key != os.getenv("ALERT_API_KEY"):
        return jsonify({'status': False, 'message': 'Yetkisiz erişim!'}), 403

    collection = db_manager.get_collection('users')
    all_users = list(collection.find())
    emails = [u.get('email') for u in all_users if u.get('email')]

    if not emails:
        return jsonify({'status': False, 'message': 'Gönderilecek mail adresi bulunamadı.'}), 404

    activity_level = 70
    data = request.get_json(silent=True)
    if data and 'activity_level' in data:
        activity_level = int(data['activity_level'])

    success_count = 0
    subject = f"KRİTİK: Güneş Aktivitesi %{activity_level}"
    content = f"Güneş aktivite seviyesi %{activity_level} eşiğini geçmiştir. Güvenli moda geçiliyor."

    for email in emails:
        if send_email_notification(email, subject, content, activity_level):
            success_count += 1

    return jsonify({
        'status': True, 
        'message': f'İşlem bitti. {success_count} mail gönderildi.'
    })

@notification_bp.route('/trigger-alert', methods=['GET', 'POST'])
def trigger_alert():
    alert_data = {
        "title": "GÜNEŞ FIRTINASI TESPİT EDİLDİ!",
        "message": "X-Sınıfı büyük bir patlama gerçekleşti. Jeomanyetik fırtına bekleniyor.",
        "level": "Kritik",
        "time": time.strftime("%H:%M:%S")
    }
    
    # Tüm bağlı clientlere bildirim gönder
    socketio.emit('solar_alert', alert_data, namespace='/')
    
    return jsonify({"status": "Başarılı", "message": "Bildirim tüm cihazlara fırlatıldı!"})