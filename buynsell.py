from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app,
)
from .filestream import upload_file_to_local, upload_file_to_s3
from . import db

bp = Blueprint('buynsell', __name__, url_prefix='/buynsell')

@bp.route('/', methods=('GET',))
def index():
    return render_template('buynsell/index.html')
    
    
@bp.route('/write', methods=('GET', 'POST'))
def write():
    return render_template('write.html')
    
    
@bp.route('/<board_name>', methods=('GET', 'POST'))
def board_list(board_name):
    if request.method == "POST":
        ## board 글쓰는 로직
        pass
    board_name = board_name.replace('\n', '').replace(' ', '')
    try:
        content_list = db.select_rows(
            "SELECT * FROM board_{}".format(board_name)
        )
    except:
        return redirect(url_for('buynsell.index'))
        
    if content_list.empty:
        content_list = None
    else:
        content_list = content_list.to_dict('records')
    return render_template('board_list.html', content_list=content_list)
    
    
@bp.route('/<board_name>/<int:board_id>', methods=('GET', 'POST'))
def board_content(board_name, board_id):
    if request.method == "POST":
        ## review 입력하는 로직
        pass
    
    board_name = board_name.replace('\n', '').replace(' ', '')
    try:
        content = db.select_row(
            "SELECT * FROM board_{} WHERE board_id = %s".format(board_name), [board_id]
        )
    except:
        return redirect(url_for('buynsell.index'))
    if not content:
        return redirect(url_for('buynsell.board_list', board_name=board_name))
    reviews = db.select_rows(
        "SELECT * FROM board_{}_review WHERE board_id = %s".format(board_name), [board_id]
    )
    
    if reviews.empty:
        reviews = None
    else:
        reviews = reviews.to_dict('records')
    
    return render_template('board_content.html', content = content, reviews=reviews)