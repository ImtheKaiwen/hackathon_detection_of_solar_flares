from app.extensions import db_manager
from bson import ObjectId  

def register_user(data: dict):
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not (username and email and password):
        return None, "Eksik bilgi girdiniz (kullanıcı adı, e-posta veya şifre eksik)."

    collection = db_manager.get_collection('user')
    
    if collection is None:
        print("Veritabanı bağlantısı yok veya koleksiyon bulunamadı.", flush=True)
        return None, "Veritabanı bağlantısı kurulamadı."
        
    existing_user = collection.find_one({
        '$or': [{'username': username}, {'email': email}]
    })
    
    if existing_user:
        return None, "Bu kullanıcı adı veya e-posta adresi zaten kullanımda."

    try:
        result = collection.insert_one({
            'username': username, 
            'email': email, 
            'password': password
        })

        if result.inserted_id:
            return str(result.inserted_id), "Kayıt başarılı."
    except Exception as e:
        print("Kayıt hatası:", e, flush=True)
        return None, f"Veritabanı hatası: {str(e)}"

    return None, "Bilinmeyen bir hata oluştu."

def login_user(data: dict):
    username = data.get('username')
    password = data.get('password')
    
    if username is None or password is None:
        return None, "Kullanıcı adı veya şifre eksik."

    collection = db_manager.get_collection("user")
    
    if collection is None:
        print("Veritabanı bağlantısı yok veya koleksiyon bulunamadı.", flush=True)
        return None, "Veritabanı bağlantısı kurulamadı."

    try:
        user = collection.find_one({'username': username, 'password': password})

        if user: 
            return str(user.get('_id')), "Giriş başarılı."
        else:
            return None, "Kullanıcı adı veya şifre hatalı."
    except Exception as e:
        print("Giriş hatası:", e, flush=True)
        return None, f"Veritabanı hatası: {str(e)}"
            
    return None, "Bilinmeyen bir hata oluştu."