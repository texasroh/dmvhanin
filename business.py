from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app,
)
from .filestream import upload_file_to_local, upload_file_to_s3
from . import db
from .auth import generate_hash, admin_only
import os

bp = Blueprint('business', __name__, url_prefix='/business')


@bp.route("/", methods=('GET', ))
def index():
    cat_list = db.select_rows(
        "SELECT * FROM business_category a "\
        "INNER JOIN business b ON a.category_id = b.category_id "\
        "ORDER BY a.category_id"
        #"SELECT * FROM business_category ORDER BY 1"
    )[['category_id', 'category1', 'category2']].drop_duplicates()
    cat_list = cat_list.loc[:, ~cat_list.columns.duplicated()]
    cat1_list = cat_list['category1'].unique()
    cat_data = {}
    for cat1 in cat1_list:
        cat_data[cat1] = cat_list[cat_list['category1'] == cat1][['category_id', 'category2']].to_dict('records')
    return render_template('business/index.html', cat_data = cat_data)

@bp.route('/list/<int:category_id>', methods=('GET', ))
def business_list(category_id):
    cat_name = db.select_row(
        "SELECT * FROM business_category WHERE category_id = %s",
        [category_id]
    )
    biz_list = db.select_rows(
        'SELECT * FROM business WHERE category_id = %s ORDER BY business_name_kor collate "ko_KR.utf8"',
        [category_id]
    )
    if not cat_name or biz_list.empty:
        return redirect(url_for('business.index'))
    biz_list = biz_list.to_dict('records')
    return render_template('business/list.html', cat_name = cat_name, biz_list=biz_list, biz_num = len(biz_list))
    

@bp.route('/<int:business_id>', methods=('GET', ))
def business_detail(business_id):
    biz = db.select_row(
        "SELECT * FROM business WHERE business_id = %s",
        [business_id]
    )
    
    if not biz:
        return redirect(url_for('business.index'))
        
    return render_template('business/detail.html', biz = biz)



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
    