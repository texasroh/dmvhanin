from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app,
)
from .dmvhaninlib.filestream import summernote_save_img_to_s3
from . import db
from .config import Config
from .auth import login_required, admin_only
from .dmvhaninlib.logging import get_client_ip
from .dmvhaninlib.paging import get_pagination
from bs4 import BeautifulSoup

bp = Blueprint('buynsell', __name__, url_prefix='/buynsell')

category = 'buynsell'

def get_board_list():
    board_list = db.select_rows(
        "SELECT * FROM board_list WHERE board_category = %s", [category]
    )
    return board_list

@bp.route('/', methods=('GET','POST'))
def index():
    board_list = get_board_list()
    return redirect(url_for('buynsell.content_list',board_name='kids'))
    #return render_template('board/index.html', board_list = board_list.to_dict('records'))
    
    
@bp.route('/write', methods=('GET', 'POST'))
@login_required
def write():
    board_list = get_board_list()
    title=''
    content=''
    if request.method == "POST":
        board = request.form['board']
        title = request.form['title']
        content = request.form['content']
        content,img_urls = summernote_save_img_to_s3(content)
        
        if not content:
            flash('잘못된 이미지파일입니다')
        elif not board:
            flash('게시판을 선택하세요')
        elif board not in list(board_list['board_name']):
            flash('존재하지 않는 게시판입니다')
        elif not title:
            flash('제목을 입력하세요')
        else:
            bs = BeautifulSoup(content, 'html.parser')
            content = str(bs).replace('<script','').replace('</script','').replace('<iframe','').replace('</iframe','')
            db.update_rows(
                "INSERT INTO {}_{} (user_id, title, contents, ip_address, image_url) VALUES (%s, %s, %s, %s, %s)".format(category, board),
                [g.user['user_id'], title, content, get_client_ip(), img_urls]
            )
            board_id = db.select_row(
               "SELECT LASTVAL()"
            )['lastval']
            flash('작성 완료')
            return redirect(url_for('{}.content'.format(category), board_name = board, board_id = board_id))
        
    return render_template('board/write.html', board_list = board_list.to_dict('records'), title=title, content=content)
    
    
@bp.route('/modify/<board_name>/<int:board_id>', methods=('GET','POST'))
@login_required
def modify(board_name, board_id):
    board_list = get_board_list()
    if board_name not in list(board_list['board_name']):
        return redirect(url_for('index'))
    content = db.select_row(
        "SELECT * FROM {}_{} WHERE active_flag = TRUE AND board_id = %s".format(category,board_name), [board_id]
    )
    if not content:
        return redirect(url_for('index'))
    elif g.user['user_id'] != content['user_id']:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form['title']
        content_textarea = request.form['content']
        content_textarea, img_urls = summernote_save_img_to_s3(content_textarea)
        
        if not content_textarea:
            flash('잘못된 이미지파일입니다')
        elif not title:
            flash('제목을 입력하세요')
        else:
            #히스토리 남기기
            db.update_rows(
                "INSERT INTO {category}_{board_name} (user_id, title, contents, ip_address, image_url, active_flag, notice_flag, views, parent_id) "\
                "SELECT user_id, title, contents, ip_address, image_url, FALSE, notice_flag, views, %s FROM {category}_{board_name} WHERE board_id = %s"
                .format(category=category, board_name=board_name),
                [board_id, board_id]
            )
            bs = BeautifulSoup(content_textarea, 'html.parser')
            content_textarea = str(bs).replace('<script','').replace('</script','').replace('<iframe','').replace('</iframe','')
            db.update_rows(
                "UPDATE {}_{} SET title=%s, contents=%s, ip_address=%s, image_url = %s WHERE board_id = %s".format(category, board_name),
                [title, content_textarea, get_client_ip(), img_urls, board_id]
            )
            flash('수정 완료')
            return redirect(url_for('{}.content'.format(category), board_name = board_name, board_id = board_id))
        
    board_alias = board_list.loc[board_list['board_name'] == board_name, 'board_alias'].to_list()[0]
    return render_template('board/write.html', board_list = board_list.to_dict('records'),
                            title=content['title'], content=content['contents'], board_alias = board_alias, modify = True)
    
 
@bp.route('/delete/<board_name>/<int:board_id>', methods=('GET','POST'))
@login_required
def delete(board_name, board_id):
    board_list = get_board_list()
    if board_name not in list(board_list['board_name']):
        return redirect(url_for('index'))
    content = db.select_row(
        "SELECT * FROM {}_{} WHERE active_flag = TRUE AND board_id = %s".format(category,board_name), [board_id]
    )
    if not content or (g.user['user_id'] != content['user_id'] and not g.user['admin_flag']):
        return redirect(url_for('index'))

    db.update_rows(
        "UPDATE {}_{} SET active_flag=FALSE WHERE board_id = %s".format(category, board_name), [board_id]
    )
    return redirect(url_for('{}.content_list'.format(category), board_name=board_name))


@bp.route('/<board_name>', methods=('GET', 'POST'))
def content_list(board_name):
    ## url injection check
    board_list = get_board_list()
    if board_name not in list(board_list['board_name']):
        return redirect(url_for('index'))
    
    search = request.args.get('search', '')
    if search:
        search_sql = "AND (a.title LIKE %s OR a.user_id LIKE %s)"
        search_param = ['%'+search+'%','%'+search+'%']
    else:
        search_sql = ''
        search_param = []
        
    curr_page = int(request.args.get('page', 1))
    total_num = db.select_row(
        "SELECT COUNT(*) FROM {0}_{1} a WHERE active_flag=TRUE {2}"
        .format(category, board_name, search_sql),
        search_param
    )['count']
    last_page = (total_num - 1) // Config.NUM_CONTENTS_PER_PAGE + 1
    page_list = get_pagination(curr_page, last_page)
    
    content_list = db.select_rows(
        "SELECT a.*, count(b.*), c.nickname FROM {0}_{1} a "\
        "LEFT JOIN {0}_{1}_review b "\
        "ON a.board_id = b.board_id "\
        "INNER JOIN user_acct c "\
        "ON a.user_id = c.user_id "\
        "WHERE a.active_flag=TRUE "\
        "{4} "\
        "GROUP BY a.board_id, c.nickname "\
        "ORDER BY notice_flag DESC, 1 DESC "\
        "LIMIT {2} OFFSET {3}"
        .format(category, board_name, Config.NUM_CONTENTS_PER_PAGE, Config.NUM_CONTENTS_PER_PAGE*(curr_page-1), search_sql),
        search_param
    )
    print(content_list['nickname'])
    
    if content_list.empty:
        content_list = None
    else:
        content_list['image_url'] = content_list['image_url'].apply(lambda x: x.split(';')[0] if x else None)
        content_list['created'] = content_list['created'].dt.tz_convert('US/Eastern').apply(lambda x: x.strftime("%Y-%m-%d"))
        content_list = content_list.to_dict('records')
    return render_template('board/content_list.html', board_list = board_list.to_dict('records'), content_list=content_list,
                            category=category, board_name=board_name, curr_page = curr_page, last_page= last_page, page_list = page_list, search=search)
    
    
@bp.route('/<board_name>/<int:board_id>', methods=('GET', 'POST'))
def content(board_name, board_id):
    ## url injection check
    board_list = get_board_list()
    if board_name not in list(board_list['board_name']):
        return redirect(url_for('index'))
        
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
    else:
        db.update_rows(
            "UPDATE {}_{} SET views = views+1 WHERE board_id = %s".format(category, board_name),
            [board_id]
        )
        
    
    content = db.select_row(
        "SELECT * FROM {}_{} a "\
        "INNER JOIN user_acct b "\
        "ON a.user_id = b.user_id "\
        "WHERE a.active_flag = TRUE AND a.board_id = %s".format(category, board_name), [board_id]
    )
    if not content:
        return redirect(url_for('{}.content_list'.format(category), board_name=board_name))
    content['created'] = content['created'].tz_convert('US/Eastern').strftime("%Y-%m-%d (%H:%M)")
    reviews = db.select_rows(
        "SELECT * FROM {}_{}_review WHERE board_id = %s ORDER BY sort".format(category, board_name), [board_id]
    )
    
    if reviews.empty:
        reviews = None
    else:
        reviews['created'] = reviews['created'].dt.tz_convert('US/Eastern').apply(lambda x: x.strftime("%Y-%m-%d (%H:%M)"))
        reviews = reviews.to_dict('records')
    return render_template('board/content.html', board_list = board_list.to_dict('records'),
                            category=category, board_name=board_name, content = content, reviews=reviews)

@bp.route('/toggle_notice/<board_name>/<int:board_id>', methods=('GET',))
@admin_only
def toggle_notice(board_name, board_id):
    db.update_rows(
        "UPDATE {}_{} SET notice_flag = NOT notice_flag WHERE board_id = %s".format(category, board_name), [board_id]
    )
    return redirect(url_for('{}.content'.format(category), board_name=board_name, board_id=board_id))

@bp.route('/review-delete/<board_name>/<int:board_id>/<int:review_id>', methods=('GET','POST'))
@login_required
def review_delete(board_name, board_id, review_id):
    board_list = get_board_list()
    if board_name not in list(board_list['board_name']):
        return redirect(url_for('index'))
    review = db.select_row(
        "SELECT * FROM {}_{}_review WHERE active_flag = TRUE AND review_id = %s".format(category,board_name), [review_id]
    )
    if not review or (g.user['user_id'] != review['user_id'] and not g.user['admin_flag']):
        return redirect(url_for('index'))

    db.update_rows(
        "UPDATE {}_{}_review SET active_flag=FALSE WHERE review_id = %s".format(category, board_name), [review_id]
    )
    return redirect(url_for('{}.content'.format(category), board_name=board_name, board_id=board_id))