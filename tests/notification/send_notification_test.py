from app.modules.notification import send_email_notification

def test_send_email_notification():
    response: dict = send_email_notification('bucocuknereli@gmail.com', 'Alert', 'Example_text')   
    assert response == True