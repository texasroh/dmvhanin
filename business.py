from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app,
)
from dmvhanin.filestream import upload_file_to_local, upload_file_to_s3

import os

bp = Blueprint('business', __name__, url_prefix='/business')


@bp.route("/", methods=('GET', ))
def index():
    pass

@bp.route('/register', methods=('GET','POST'))
def register():
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
        for i in range(5):
            file = request.files['file'+str(i+1)]
            if file.filename == '':
                continue
            path = upload_file_to_local(file, business_name_eng+str(i+1)+file.filename)
            if path:
                img_list.append(path)
                
        img_list = ';'.join(img_list)
    
    return render_template('business/register.html')
    
@bp.route('/test', methods=('GET',))
def test():
    return url_for('static', filename='css/style.css')
