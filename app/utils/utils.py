from flask import session

def get_current_user():
    if 'user_id' in session:
        return session.get('user_id')
    return None

def start_session(user_id : str):
    session['user_id'] = user_id

def end_session():
    session.pop('user_id', None)

def is_session_active() -> bool:
    return bool(session.get('user_id'))

        