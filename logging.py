import os
from .config import Config


def logging(msg, file='default.log'):
    with open(os.path.join(Config.LOG_DIC_PATH, file), 'a') as f:
        f.write(msg)