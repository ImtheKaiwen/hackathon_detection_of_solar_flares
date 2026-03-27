from flask import Blueprint, request, render_template, jsonify, redirect
from .service import login_user, register_user
from app.utils import end_session, get_current_user, start_session, is_session_active

user_bp = Blueprint("user", __name__)

@user_bp.route('/login', methods=['GET','POST'])
def login():
    
    if request.method == 'GET':
        return render_template('login.html')
    
    if request.method == 'POST':
        data = request.get_json()
        user_id, message = login_user(data)
        
        if user_id:
            start_session(user_id)
            return jsonify({'user_id': user_id, 'status': True, 'message': message})
        
        return jsonify({'user_id': None, 'status': False, 'message': message})
    
    if is_session_active():
        return redirect('/dashboard')


@user_bp.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'GET':
        return render_template('register.html')
    
    if is_session_active():
        return redirect('/dashboard')
    
    data = request.get_json()
    user_id, message = register_user(data)

    if user_id:
        return jsonify({'user_id': user_id, 'status': True, 'message': message})
    
    return jsonify({'user_id': None, 'status': False, 'message': message})

@user_bp.route('/logout', methods=['GET'])
def logout():
    end_session()
    return redirect('/')