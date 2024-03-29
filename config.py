from os import environ
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

class Config:

    NOT_ALLOWED_USER_ID = ['admin', 'administrator', 'representative', '관리자', '어드민', '디엠비한인', '디엠비hanin', 'dmvhanin', 'dmv한인']

    # Database config
    DB_HOST=environ.get('DB_HOST')
    DB_NAME=environ.get('DB_NAME')
    DB_USER=environ.get('DB_USER')
    DB_PWD=environ.get('DB_PWD')
    DB_PORT=environ.get('DB_PORT')
    
    # gmail SMTP config
    GMAIL_ACCT=environ.get('GMAIL_ACCT')
    GMAIL_PWD=environ.get('GMAIL_PWD')
    GMAIL_SMTP=environ.get('GMAIL_SMTP')
    GMAIL_PORT=environ.get('GMAIL_PORT')
    
    # salt value
    SALT=environ.get('SALT')
    
    # filestream
    ALLOWED_EXTENSIONS = {'png','jpg','jpeg'}
    LOG_DIC_PATH = 'logs'
    TMP_DIC = 'tmp'
    
    # board
    NUM_CONTENTS_PER_PAGE = 15
    
    # auth
    AUTH_KEY=environ.get('AUTH_KEY')