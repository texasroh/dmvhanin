from flask import render_template, Blueprint, g, flash, redirect, url_for, request
from . import db
import pandas as pd

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.before_request
def check_admin():
    if not g.user or not g.user['admin_flag']:
        flash('Access Denied')
        return redirect(url_for('index'))

@bp.route('/', methods=('GET',))
def index():
    num_business_request = db.select_row(
        "SELECT COUNT(*) FROM business_register_request WHERE active_flag = TRUE and verified = FALSE"
    )['count']
    return render_template('admin/index.html', num_business_request = num_business_request)
    
@bp.route('/business_req_list', methods=('GET', ))
def business_request_list():
    business_list = db.select_rows(
        "SELECT * FROM business_register_request WHERE active_flag = TRUE and verified = FALSE"
    )
    if business_list.empty:
        business_list = None
    else:
        business_list['created_date'] = business_list['created_date'].dt.tz_convert('US/Eastern').apply(lambda x: x.strftime("%Y-%m-%d (%H:%M)"))
        business_list = business_list.to_dict('index')
    return render_template('admin/business_list.html', business_list = business_list)
    
    
@bp.route('/business_req_detail/<int:request_id>', methods=('GET', 'POST'))
def business_request_detail(request_id):
    if request.method == "post":
        decision = request.form['decision']
        if decision == 'approve':
            category_id = request.form['category_id']
        else:
            reason = request.form['reason']
            
        return redirect(url_for('admin.business_request_list'))

            
            
    business = db.select_row(
        "SELECT * FROM business_register_request WHERE active_flag = TRUE and verified = FALSE and request_id = %s", [request_id]
    )
    img_list = business['images']
    if img_list:
        img_list = img_list.split(';')
        img_name = [img.split('-',3)[-1] for img in img_list]
        img_data = pd.DataFrame({'name': img_name, 'path':img_list}).to_dict('index')
    else:
        img_data = None
    business = {k:v if v else '-------' for k, v in business.items()}
    return render_template('admin/business_detail.html', business = business, img_data = img_data)