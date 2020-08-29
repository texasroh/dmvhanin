import os
from .config import Config
from datetime import datetime
from flask import request


def logging(msg, file='default.log'):
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    with open(os.path.join(Config.LOG_DIC_PATH, file), 'a') as f:
        f.write(str(datetime.now()) + ' - ' + ip + ' - ' + msg + '\n')