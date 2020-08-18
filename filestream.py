from .config import Config
from werkzeug.utils import secure_filename
import os

def allowed_file(filename):
    valid = '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    if valid: 
        filename = secure_filename(filename)
    else:
        filename = ''
    return valid, filename
    
def upload_file_to_local(file, filename):
    valid, filename = allowed_file(filename)
    if not valid:
        return False

    if Config.OS == 'windows':
        file.save(filename)
        image_path = filename
    elif Config.OS == 'linux':
        path = os.path.join(os.path.dirname(__file__), Config.UPLOAD_FOLDER)
        file.save(Config.UPLOAD_FOLDER, filename)
        image_path = os.path.join(Config.UPLOAD_FOLDER, filename)

    return image_path
    
def upload_file_to_s3(file, filename):
    valid, filename = allowed_file(filename)
    if not valid:
        return False
    # s3 에 올리기
    # image_url = s3 링크
    return image_url