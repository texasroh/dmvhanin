from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app,
)

from . import db

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.before_request
def check_admin():
    if not g.user or not g.user['admin_flag']:
        flash('Access Denied')
        return redirect(url_for('index'))
        
@bp.route('/business_request_list', methods=('GET', 'POST'))
def business_request_list():
    if request.method == 'POST':
        pass
        
    request_list = db.select_rows(
        "SELECT * FROM business_register_request WHERE active_flag=TRUE AND verified=FALSE"
    )
    
    num_request_list = len(request_list)
    
    return 'a'