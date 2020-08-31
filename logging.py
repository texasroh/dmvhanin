import os
from .config import Config
from datetime import datetime
from flask import request

def get_client_ip():
    return request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

def logging(msg, file='default.log'):
    ip = get_client_ip()
    with open(os.path.join(Config.LOG_DIC_PATH, file), 'a') as f:
        f.write(str(datetime.now()) + ' - ' + ip + ' - ' + msg + '\n')