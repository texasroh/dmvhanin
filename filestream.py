from flask import current_app, url_for, g
from .config import Config
from werkzeug.utils import secure_filename
import os
import io
import base64
import boto3
from bs4 import BeautifulSoup
from datetime import datetime

def allowed_file(filename):
    valid = '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    if valid: 
        filename = secure_filename(filename)
    else:
        filename = ''
    return valid, filename
    
def upload_file_to_tmp_local(file, file_name):
    valid, filename = allowed_file(file_name)
    if not valid:
        return False
    file_name = '{}-{}'.format(datetime.now().strftime("%y%m%d%H%M%S"), file_name)
    file_path = '/static/'+Config.TMP_DIC+'/'+file_name
    file.save('webdocs'+file_path)
    return file_path
    
def delete_local_file(filepath):
    try:
        os.remove(filepath)
    except:
        #log 남기기
        return False
    return True
    
def upload_file_to_s3(file_path, folder='', bucket = 'dmvhanin'):
    if '/' in file_path:
        file_name = file_path.rsplit('/',1)[1]
    else:
        file_name = file_path
    valid, file_name = allowed_file(file_name)
    if not valid:
        return False
    
    if folder:
        folder = folder + '/'
    # s3 에 올리기
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_path, bucket, folder+file_name)
    except:
        # 로그 필요
        return False
    
    # image_url = s3 링크
    image_url = "https://{}.s3.amazonaws.com/{}".format(bucket, folder+file_name)
    return image_url


def upload_fileobj_to_s3(file_name, file_obj, folder='', bucket='dmvhanin'):
    s3_client = boto3.client('s3')
    if folder:
        folder = folder + '/'
    
    try:
        s3_client.upload_fileobj(file_obj, bucket, folder+file_name)
    except:
        return False
    
    image_url = "https://{}.s3.amazonaws.com/{}".format(bucket,folder+file_name)
    return image_url
    
    
def summernote_save_img_to_s3(content):
    bs = BeautifulSoup(content, 'html.parser')
    imgs = bs.find_all('img')
    
    for img in imgs:
        if ',' not in img.attrs['src'] or 'base64' not in img.attrs['src']: continue
        code = img.attrs['src'].split(',')[1]
        file_name = img.attrs['data-filename']
        valid, file_name = allowed_file(file_name)
        if not valid:
            return False
        else:
            file_name = '{}-{}-{}'.format(datetime.now().strftime("%y%m%d%H%M%S"), g.user['user_id'], file_name)
            
        b = base64.b64decode(code)
        with io.BytesIO(b) as f:
            url = upload_fileobj_to_s3(file_name, f, 'board_pics')
            
        if not url:
            url = ''
        img.attrs['src'] = url
        
    return str(bs)