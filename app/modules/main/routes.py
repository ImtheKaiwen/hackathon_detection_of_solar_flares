from flask import Blueprint, render_template, request, redirect,url_for
from app.utils import is_session_active

main_bp = Blueprint("main", __name__)

# SECURE_PAGES = ['dashboard']
# PUBLIC_PAGES = ['login', 'register', 'index']


@main_bp.route("/", methods=['GET'])
def index():
    return render_template("index.html")

@main_bp.route("/dashboard", methods=['GET'])
def dashboard():
    # if is_session_active():
    #     return render_template('dashboard.html')
    # return redirect('/login')
    return render_template('dashboard.html')

@main_bp.route("/info", methods=['GET'])
def info():
    return render_template('info.html')

@main_bp.route('/about', methods=['GET'])
def abouth():
    return render_template('about.html')