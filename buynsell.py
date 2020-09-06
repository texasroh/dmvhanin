from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app,
)
from .filestream import upload_file_to_local, upload_file_to_s3
from . import db
from .auth import login_required
from .logging import get_client_ip
from bs4 import BeautifulSoup

bp = Blueprint('buynsell', __name__, url_prefix='/buynsell')

category = 'buynsell'

def get_board_list():
    board_list = db.select_rows(
        "SELECT * FROM board_list WHERE board_category = %s", [category]
    )
    return board_list

@bp.route('/', methods=('GET',))
def index():
    board_list = get_board_list()

    return render_template('board/index.html', board_list = board_list.to_dict('records'))
    
    
@bp.route('/write', methods=('GET', 'POST'))
@login_required
def write():
    board_list = get_board_list()
    if request.method == "POST":
        board = request.form['board']
        title = request.form['title']
        content = request.form['content']
        if not board:
            flash('게시판을 선택하세요')
        elif board not in list(board_list['board_name']):
            flash('존재하지 않는 게시판입니다')
        elif not title:
            flash('제목을 입력하세요')
        else:
            bs = BeautifulSoup(content)
            content = str(bs).replace('<script>','').replace('</script>','')
            db.update_rows(
                "INSERT INTO {}_{} (user_id, title, contents, ip_address) VALUES (%s, %s, %s, %s)".format(category, board),
                [g.user['user_id'], title, content, get_client_ip()]
            )
            flash('작성 완료')
            return redirect(url_for('{}.content_list'.format(category), board_name = board))
        
    return render_template('board/write.html', board_list = board_list.to_dict('records'))
    
    
@bp.route('/<board_name>', methods=('GET', ))
def content_list(board_name):
    ## url injection check
    board_list = get_board_list()
    if board_name not in list(board_list['board_name']):
        return redirect(url_for('index'))
    content_list = db.select_rows(
        "SELECT * FROM {}_{} ORDER BY 1 DESC".format(category, board_name)
    )
    if content_list.empty:
        content_list = None
    else:
        content_list['created'] = content_list['created'].dt.tz_convert('US/Eastern').apply(lambda x: x.strftime("%Y-%m-%d"))
        content_list = content_list.to_dict('records')
    return render_template('board/content_list.html', board_list = board_list.to_dict('records'), content_list=content_list,
                            category=category, board_name=board_name)
    
    
@bp.route('/<board_name>/<int:board_id>', methods=('GET', 'POST'))
def content(board_name, board_id):
    ## url injection check
    board_list = get_board_list()
    if board_name not in list(board_list['board_name']):
        return redirect(url_for('index'))
    elif not db.select_row("SELECT * FROM {}_{} WHERE board_id = %s".format(category,board_name), [board_id]): 
        return redirect(url_for('{}.content_list'.format(category), board_name=board_name))
        
    if request.method == "POST":
        ## review 입력하는 로직
        if not g.user:
            flash('로그인이 필요합니다.')
            return redirect(url_for('{}.content'.format(category), board_name=board_name, board_id=board_id))
        ## 계층형 댓글 구현
        comment = request.form['comment']
        sort = int(request.form['sort'])
        depth = int(request.form['depth'])
        
        coalesce = int(db.select_row(
            "SELECT COALESCE(MIN(sort), 0) FROM {}_{}_review "\
            "WHERE board_id = %s AND sort > %s AND depth <= %s ".format(category, board_name),
            [board_id, sort, depth]
        )['coalesce'])

        if coalesce is 0:
            sort = int(db.select_row(
                "SELECT COALESCE(MAX(sort), 0) + 1 AS coalesce FROM {}_{}_review "\
                "WHERE board_id = %s".format(category, board_name),
                [board_id]
            )['coalesce'])
            
        else:
            sort = coalesce
            db.update_rows(
                "UPDATE {}_{}_review SET sort = sort + 1 "\
                "WHERE board_id = %s and sort >= %s".format(category, board_name),
                [board_id, sort]
            )
            
        db.update_rows(
            "INSERT INTO {}_{}_review (board_id, comment, ip_address, user_id, sort, depth) "\
            "VALUES (%s, %s, %s, %s, %s, %s)".format(category, board_name),
            [board_id, comment, get_client_ip(), g.user['user_id'], sort, depth+1]
        )
        
        #redirect(url_for('{}.content'.format(category), board_name=board_name, board_id=board_id))
    
    content = db.select_row(
        "SELECT * FROM {}_{} WHERE board_id = %s".format(category, board_name), [board_id]
    )
    if not content:
        return redirect(url_for('buynsell.board_list', board_name=board_name))
    content['created'] = content['created'].tz_convert('US/Eastern').strftime("%Y-%m-%d %H:%M")
    reviews = db.select_rows(
        "SELECT * FROM {}_{}_review WHERE board_id = %s ORDER BY sort".format(category, board_name), [board_id]
    )
    
    if reviews.empty:
        reviews = None
    else:
        reviews['created'] = reviews['created'].dt.tz_convert('US/Eastern').apply(lambda x: x.strftime("%Y-%m-%d %H:%M"))
        reviews = reviews.to_dict('records')
    return render_template('board/content.html', board_list = board_list.to_dict('records'), content = content, reviews=reviews)
    