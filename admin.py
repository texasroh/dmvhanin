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
    num_active_tip = db.select_row(
        "SELECT COUNT(*) FROM tip WHERE active_flag = TRUE AND confirm=FALSE"
    )['count']
    return render_template('admin/index.html', num_business_request = num_business_request, num_active_tip = num_active_tip)
    
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
    if request.method == "POST":
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
    
    
@bp.route('/agent-manage', methods=('GET','POST'))
def agent_manage():
    if request.method=='POST':
        div = request.form['div']
        id = request.form['id']
        db.update_rows(
            "UPDATE {div} SET active_flag=FALSE WHERE {div}_id = %s".format(div=div),
            [id]
        )
        return redirect('admin.agent_manage')
        
    agents = db.select_rows(
        "SELECT 'realtor' AS div, realtor_id AS id, name, company, phone, email "\
        "FROM realtor "\
        "WHERE active_flag=TRUE "\
        "UNION ALL "\
        "SELECT 'dealer' AS div, dealer_id AS id, name, company, phone, email "\
        "FROM dealer "
        "WHERE active_flag=TRUE "\
        "ORDER BY div DESC, id "\
    )
    if agents.empty:
        agents = None
    else:
        agents = agents.to_dict('index')
    return render_template('admin/agent_manage.html', agents = agents)
    

@bp.route('/agent-create', methods=('GET','POST'))
def agent_create():
    if request.method == 'POST':
        name = request.form['name']
        company = request.form['company']
        phone = request.form['phone']
        email = request.form['email']
        div = request.form['div']
        
        db.update_rows(
            "INSERT INTO {div} (name, company, phone, email) "\
            "VALUES (%s, %s, %s, %s)".format(div=div), [name, company, phone, email]
        )
        return redirect(url_for('admin.agent_manage'))
        
    return render_template('admin/agent_create.html', create=True)
    
@bp.route('/agent-modify/<div>/<int:id>', methods=('GET','POST'))
def agent_modify(div, id):
    if request.method == 'POST':
        name = request.form['name']
        company = request.form['company']
        phone = request.form['phone']
        email = request.form['email']
        div = request.form['div']
        
        db.update_rows(
            "UPDATE {div} SET name=%s, company=%s, phone=%s, email=%s WHERE {div}_id = %s".format(div=div), 
            [name, company, phone, email, id]
        )
        return redirect(url_for('admin.agent_manage'))
        
    agent = db.select_row(
        "SELECT * FROM {div} WHERE {div}_id= %s".format(div=div), [id]
    )
        
    return render_template('admin/agent_create.html', modify=True, agent=agent, div=div)
    
    
@bp.route('/tip', methods=('GET',))
def tip():
    tips = db.select_rows(
        "SELECT * FROM tip "\
        "WHERE active_flag = TRUE "\
        "ORDER BY confirm DESC, tip_id"
    )
    if tips.empty:
        tips = None
    else:
        tips = tips.to_dict('index')
    
    return render_template('admin/tip_list.html', tips = tips)