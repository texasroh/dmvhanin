from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app,
)
from dmvhanin.filestream import upload_file_to_local, upload_file_to_s3
from dmvhanin import db
from .auth import generate_hash
import os

bp = Blueprint('business', __name__, url_prefix='/business')


@bp.route("/", methods=('GET', ))
def index():
    return redirect(url_for('index'))

@bp.route('/register_request', methods=('GET','POST'))
def register_request():
    if request.method == 'POST':
        business_name_kor = request.form['business_name_kor']
        business_name_eng = request.form['business_name_eng']
        phone_number = request.form['phone_number']
        email = request.form['email']
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        zipcode = request.form['zipcode']
        homepage = request.form['homepage']
        description = request.form['description']
        
        #이미지 저장
        img_list = []
        idx = 0
        for i in range(5):
            file = request.files['file'+str(i+1)]
            if file.filename == '':
                continue
            idx += 1
            hash=generate_hash()[:5]
            path = upload_file_to_local(file, hash+'-'+business_name_eng+'-'+str(idx)+'-'+file.filename)
            if path:
                img_list.append(path)
                
        img_list = ';'.join(img_list)
        
        db.update_rows(
            "INSERT INTO business_register_request (business_name_kor, business_name_eng, address, city, state, zipcode, phone_number, description, images, email) "\
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [business_name_kor, business_name_eng, address, city, state, zipcode, phone_number, description, img_list, email]
        )
        return redirect(url_for('thank', s='request'))
    
    return render_template('business/request.html')
    
@bp.route('/test', methods=('GET',))
def test():
    return url_for('static', filename='css/style.css')
