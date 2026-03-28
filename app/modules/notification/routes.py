import os
from flask import Blueprint, request, jsonify
from app.modules.notification.service import send_email_notification
from app.extensions import db_manager

notification_bp = Blueprint('notification', __name__, url_prefix='/notify')

@notification_bp.route('/alert', methods=['POST'])
def alert():
    # 🔐 API Key Kontrolü
    api_key = request.headers.get('X-API-KEY')
    if api_key != os.getenv("ALERT_API_KEY"):
        return jsonify({'status': False, 'message': 'Yetkisiz erişim!'}), 403

    # 🗄️ Veritabanından Kullanıcıları Çek
    collection = db_manager.get_collection('users')
    all_users = list(collection.find())
    emails = [u.get('email') for u in all_users if u.get('email')]

    if not emails:
        return jsonify({'status': False, 'message': 'Gönderilecek mail adresi bulunamadı.'}), 404

    # 📈 Aktivite Seviyesini Al (Yoksa varsayılan 70)
    activity_level = 70
    data = request.get_json(silent=True) # 400 hatasını önlemek için silent=True yaptık
    if data and 'activity_level' in data:
        activity_level = int(data['activity_level'])

    success_count = 0
    subject = f"⚠️ KRİTİK: Güneş Aktivitesi %{activity_level}"
    content = f"Güneş aktivite seviyesi %{activity_level} eşiğini geçmiştir. Güvenli moda geçiliyor."

    for email in emails:
        if send_email_notification(email, subject, content, activity_level):
            success_count += 1

    return jsonify({
        'status': True, 
        'message': f'İşlem bitti. {success_count} mail gönderildi.'
    })