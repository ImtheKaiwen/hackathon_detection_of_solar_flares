from app.modules.user.service import login_user, register_user
from app.core import DatabaseManager
import pytest
from dotenv import load_dotenv
import uuid
import os

load_dotenv()

@pytest.fixture(scope='module')
def user_collection():
    '''
        Initializing mock database for first time. 
    '''
    db_manager = DatabaseManager()
    uri = os.getenv('MONGO_URI')
    db_name = os.getenv('DB_NAME')

    if not uri:
        pytest.fail('MONGO_URI not found')

    db_manager.init_database(uri, db_name)
    return db_manager.db['user']

def test_register_user(user_collection):
    
    unique_id = str(uuid.uuid4())[:8]
    test_username = f'user{unique_id}'

    register_credentials = {
        'username' : test_username,
        'email' : f'{test_username}@gmail.com',
        'password' : '123456789'
    }
    user_id, message =  register_user(data=register_credentials, collection=user_collection)

    assert user_id is not None


def test_login_user(user_collection):

    unique_id = str(uuid.uuid4())[:8]
    test_username = f'user_{unique_id}'

    register_user(data={
        'username' : test_username,
        'email' : f'{test_username}@gmail.com',
        'password' : '123456789'
    }, collection=user_collection)

    login_credentials = {'username': test_username, 'password': '123456789'}
    user_id, message = login_user(data=login_credentials, collection=user_collection)
    
    assert user_id is not None