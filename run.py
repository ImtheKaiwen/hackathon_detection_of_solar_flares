from app import create_app
from app.extensions import socketio
import os

if __name__ == "__main__":
    app = create_app()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)