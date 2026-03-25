import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.modules.notification.service import send_email_notification

send_email_notification('bucocuknereli@gmail.com', 'uyarı', 'deneme')   
