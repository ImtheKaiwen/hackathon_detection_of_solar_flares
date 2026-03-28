import os
from flask import Blueprint, request, jsonify
from app.modules.notification.service import send_email_notification
from app.extensions import db_manager

notification_bp = Blueprint('notification', __name__, url_prefix='/notify')

@notification_bp.route('/alert', methods=['POST'])
def alert():
    # 🔐 GÜVENLİK ADIMI (Arkadaşının istediği Key Gömme)
    # İstek atan kişinin Header'ında 'X-API-KEY' var mı ve doğru mu?
    api_key = request.headers.get('X-API-KEY')
    expected_key = os.getenv("ALERT_API_KEY") # .env dosyana ALERT_API_KEY=senin_sifren yazmalısın

    if not api_key or api_key != expected_key:
        return jsonify({
            'status': False, 
            'message': 'Yetkisiz erişim! Geçersiz güvenlik anahtarı.'
        }), 403

    # 🗄️ VERİTABANI BAĞLANTISI
    collection = db_manager.get_collection('users')
    if collection is None:
        return jsonify({'status': False, 'message': 'Veritabanı bağlantı hatası'}), 500
    
    all_users = list(collection.find())
    emails = [user.get('email') for user in all_users if user.get('email')]

    if not emails:
        return jsonify({'status': False, 'message': 'Sistemde e-posta gönderilecek kullanıcı bulunamadı.'}), 404

    # 📧 GÜNEŞ PATLAMASI BİLDİRİM DÖNGÜSÜ
    success_count = 0
    status_list = []
    
    # Profesyonel Başlık ve İçerik
    subject = "⚠️ KRİTİK: Güneş Patlaması Aktivitesi Tespit Edildi"
    message_content = "Güneş aktivite seviyesi %70 eşiğini geçmiştir. Lütfen tüm sistemleri güvenli moda alın."

    for email in emails:
        try:
            # Service içindeki fonksiyonu çağırıyoruz (O zaten loglama yapacak)
            response = send_email_notification(email, subject, message_content)
            
            if response:
                status_list.append({'status': True, 'email': email})
                success_count += 1
            else:
                status_list.append({'status': False, 'email': email})
        except Exception as e:
            status_list.append({'status': False, 'email': email})
            print(f"Hata: {email} adresine mail gönderilemedi. Sebep: {e}")

    return jsonify({
        'status': True, 
        'message': f'İşlem tamamlandı. {len(emails)} kişiden {success_count} kişiye Beacon of Helios uyarısı iletildi.',
        'data': status_list
    })