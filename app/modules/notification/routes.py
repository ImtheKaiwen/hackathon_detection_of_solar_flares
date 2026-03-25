from flask import Blueprint, request, jsonify
from app.modules.notification.service import send_email_notification
from app.utils import is_session_active
from app.extensions import db_manager

notification_bp = Blueprint('notification', __name__, url_prefix='/notify')

@notification_bp.route('/send_notification', methods=['POST'])
def send_notification():
    # if not is_session_active():
    #     return jsonify({'status' : False, 'message': 'lütfen önce giriş yapınız'})
    
    data = request.get_json()
    
    user_email = data.get('email') if data else None

    if not user_email:
        return jsonify({'status': False, 'message': 'Email boş veya bulunamadı'}), 400

    response = send_email_notification(user_email, 'uyarı', 'deneme')
    
    if response: 
        return jsonify({'status': True, 'message': 'E-posta iletimi başarılı'})
    
    return jsonify({'status': False, 'message': 'Gönderim sırasında bilinmeyen bir hata oluştu'}), 500


@notification_bp.route('/alert', methods=['POST'])
def alert():
    # if not is_session_active():
    #     return jsonify({'status': False, 'message': 'Bu işlemi yapmaya yetkiniz yok'}), 403

    collection = db_manager.get_collection('user')
    if collection is None:
        return jsonify({'status': False, 'message': 'Veritabanı bağlantı hatası'}), 500
    
    all_users = collection.find()
    
    emails = [user.get('email') for user in all_users if user.get('email')]

    if not emails:
        return jsonify({'status': False, 'message': 'Sistemde e-posta gönderilecek kullanıcı bulunamadı.'}), 404

    success_count = 0
    status = []
    for email in emails:
        try:
            response = send_email_notification(email, 'Sistem Uyarısı', 'Duyuru içeriği...')
            if response:
                status.append({'status' : True, 'email' : email})
                success_count += 1
        except Exception as e:
            status.append({'status' : False, 'email' :email})
            print(f"Hata: {email} adresine mail gönderilemedi. Sebep: {e}")
            

    return jsonify({
        'status': True, 
        'message': f'İşlem tamamlandı. {len(emails)} kişiden {success_count} kişiye bildirim başarıyla iletildi.',
        'data' : status
    })

    