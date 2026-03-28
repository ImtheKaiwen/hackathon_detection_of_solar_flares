from bson import ObjectId  

def register_user(data: dict, collection):
    name = data.get('name', '').strip()
    surname = data.get('surname', '').strip()
    email = data.get('email', '').lower().strip()

    if not (name and surname and email):
        return None, "Eksik bilgi girdiniz."

    if "@" not in email:
        return None, "Geçerli bir e-posta girin."

    if collection is None:
        print("Veritabanı bağlantısı yok.", flush=True)
        return None, "Veritabanı bağlantısı kurulamadı."

    existing_user = collection.find_one({'email': email})

    if existing_user:
        return None, "Bu e-posta adresi zaten kayıtlı."

    try:
        result = collection.insert_one({
            'name': name,
            'surname': surname,
            'email': email
        })

        if result.inserted_id:
            return str(result.inserted_id), "Kayıt başarılı."

    except Exception as e:
        print("Kayıt hatası:", e, flush=True)
        return None, f"Veritabanı hatası: {str(e)}"

    return None, "Bilinmeyen bir hata oluştu."

# def login_user(data: dict, collection):
#     name = data.get('name')
#     surname = data.get('surname')
#     email = data.get('email')
    
#     if name is None or surname is None or email is None:
#         return None, "Lütfen tüm alanları doldurunuz."

#     if collection is None:
#         print("Veritabanı bağlantısı yok veya koleksiyon bulunamadı.", flush=True)
#         return None, "Veritabanı bağlantısı kurulamadı."

#     try:
#         user = collection.find_one({'name': name, 'surname': surname,'email' : email})

#         if user: 
#             return str(user.get('_id')), "Giriş başarılı."
#         else:
#             return None, "bilgilerden birisi hatalı"
#     except Exception as e:
#         print("Giriş hatası:", e, flush=True)
#         return None, f"Veritabanı hatası: {str(e)}"