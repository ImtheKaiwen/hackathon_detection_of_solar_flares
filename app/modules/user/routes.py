from flask import Blueprint, request, jsonify, render_template
from .service import register_user
from app.extensions import db_manager

user_bp = Blueprint("user", __name__)

# @user_bp.route('/login', methods=['GET','POST'])
# def login():
    
#     if request.method == 'GET':
#         return render_template('login.html')
    
#     if request.method == 'POST':
#         data = request.get_json()
#         user_id, message = login_user(data)
        
#         if user_id:
#             start_session(user_id)
#             return jsonify({'user_id': user_id, 'status': True, 'message': message})
        
#         return jsonify({'user_id': None, 'status': False, 'message': message})
    
#     if is_session_active():
#         return redirect('/dashboard')


@user_bp.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'GET':
        return render_template('register.html')

    data = request.get_json()

    if not data:
        return jsonify({
            'user_id': None,
            'status': False,
            'message': 'Geçersiz veri gönderildi.'
        }), 400

    user_id, message = register_user(
        data,
        db_manager.get_collection('user')
    )

    if user_id:
        return jsonify({
            'user_id': user_id,
            'status': True,
            'message': message
        }), 201

    return jsonify({
        'user_id': None,
        'status': False,
        'message': message
    }), 400

# @user_bp.route('/logout', methods=['GET'])
# def logout():
#     end_session()
#     return redirect('/')