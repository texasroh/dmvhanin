from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app,
)
from .dmvhaninlib.filestream import upload_file_to_tmp_local, upload_file_to_s3
from . import db
from .auth import generate_hash, admin_only
from .dmvhaninlib.logging import get_client_ip
import os
from bs4 import BeautifulSoup

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
        "SELECT a.*, b.avg_rate FROM business a "\
        "LEFT JOIN "\
        "   (SELECT business_id, AVG(rate::float) as avg_rate "\
        "    FROM business_review WHERE rate IS NOT NULL GROUP BY business_id) b "\
        "ON a.business_id = b.business_id "\
        "WHERE category_id = %s "\
        'ORDER BY -b.avg_rate, business_name_kor collate "ko_KR.utf8"',
        [category_id]
    )
    if not cat_name or biz_list.empty:
        return redirect(url_for('business.index'))
    biz_list = biz_list.fillna('').to_dict('index')
    return render_template('business/list.html', cat_name = cat_name, biz_list=biz_list, biz_num = len(biz_list))
    

@bp.route('/<int:business_id>', methods=('GET', 'POST'))
def business_detail(business_id):
    biz = db.select_row(
        "SELECT * FROM business WHERE business_id = %s",
        [business_id]
    )
    
    if not biz:
        return redirect(url_for('business.index'))
        
    if request.method=='POST':
        if not g.user:
            flash('로그인이 필요합니다.')
            return redirect(url_for('business.business_detail', business_id = business_id))
        ##리뷰 입력작업
        rate = request.form.get('rate', None)
        comment = request.form['comment']
        sort = int(request.form['sort'])
        depth = int(request.form['depth'])
        
        coalesce = int(db.select_row(
            "SELECT COALESCE(MIN(sort), 0) FROM business_review "\
            "WHERE business_id = %s AND sort > %s AND depth <= %s ",
            [business_id, sort, depth]
        )['coalesce'])

        if coalesce is 0:
            sort = int(db.select_row(
                "SELECT COALESCE(MAX(sort), 0) + 1 AS coalesce FROM business_review "\
                "WHERE business_id = %s",
                [business_id]
            )['coalesce'])
            
        else:
            sort = coalesce
            db.update_rows(
                "UPDATE business_review SET sort = sort + 1 "\
                "WHERE business_id = %s and sort >= %s",
                [business_id, sort]
            )
            
        db.update_rows(
            "INSERT INTO business_review (business_id, rate, comment, ip_address, user_id, sort, depth) "\
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [business_id, rate, comment, get_client_ip(), g.user['user_id'], sort, depth+1]
        )
        
    
    reviews = db.select_rows(
        "SELECT * FROM business_review WHERE business_id = %s ORDER BY sort",
        [business_id]
    )
    if reviews.empty:
        reviews = None
    else:
        reviews = reviews.fillna('')
        reviews['created'] = reviews['created'].dt.tz_convert('US/Eastern').apply(lambda x: x.strftime("%Y-%m-%d %H:%M"))
        reviews = reviews.to_dict('records')
    
    return render_template('business/detail.html', biz = biz, reviews = reviews)



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
        if description:
            description = BeautifulSoup(description).text
        
        #이미지 저장
        img_list = []
        idx = 0
        for i in range(5):
            file = request.files['file'+str(i+1)]
            if file.filename == '':
                continue
            idx += 1
            path = upload_file_to_tmp_local(file, business_name_eng+'-'+str(idx)+'-'+file.filename)
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
    