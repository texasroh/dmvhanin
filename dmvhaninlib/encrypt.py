import jwt
from webdocs.config import Config

def register_decode(code):
    return jwt.decode(code, Config.AUTH_KEY, algorithms=['HS256'])
    
def register_encode(dict_obj):
    return jwt.encode(dict_obj, Config.AUTH_KEY)