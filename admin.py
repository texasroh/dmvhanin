from flask import render_template, Blueprint
from . import db

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/', methods=('GET',))
def index():
    num_business_request = db.select_row(
        "SELECT COUNT(*) FROM business_register_request"
    )['count']
    return render_template('admin/index.html', num_business_request = num_business_request)
    
@bp.route('/business', methods=('GET', ))
def business():
    business_list = db.select_rows(
        "SELECT * FROM business_register_request WHERE active_flag = TRUE and verified = FALSE"
    )
    if business_list.empty:
        business_list = None
    else:
        business_list['created_date'] = business_list['created_date'].dt.tz_convert('US/Eastern').apply(lambda x: x.strftime("%Y-%m-%d (%H:%M)"))
        business_list = business_list.to_dict('index')
    return render_template('admin/business_list.html', business_list = business_list)