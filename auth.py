import functools
from datetime import datetime, timedelta
import hashlib

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, gmail
from .config import Config
from .dmvhaninlib.logging import logging

salt = Config.SALT

bp = Blueprint('auth', __name__, url_prefix='/auth')

def generate_hash(s=''):
    myStr = str(datetime.now())+s+salt
    myHash = hashlib.sha256(str(myStr).encode('utf-8')).hexdigest()
    return myHash

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if g.user:
        return redirect(url_for('index'))
    if request.method=='POST':
        user_id = request.form['user_id']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email_addr = request.form['email']
        error = None

        
        if db.select_row(
            "SELECT user_id FROM user_acct WHERE user_id = %s", [user_id]
        ):
            error = '이미 사용중인 아이디입니다.'
        elif not user_id:
            error = '아이디를 입력하세요.'
        elif len(user_id) < 4:
            error = '최소 4자가 필요합니다.'
        elif not password:
            error = '비밀번호를 입력하세요.'
        elif password != confirm_password:
            error = '비밀번호가 일치하지 않습니다.'
        elif email_addr and db.select_row(
            "SELECT user_id FROM user_acct WHERE email = %s", [email_addr]
        ):
            error = '이미 사용중인 이메일입니다.'
        
            
        if error is None:
            db.update_rows(
                "INSERT INTO user_acct (user_id, password, email)"\
                " VALUES (%s, %s, %s)",
                [user_id, generate_password_hash(password+salt), email_addr]
            )
            
            if email_addr:
                hash = generate_hash(user_id)
                db.update_rows(
                    "INSERT INTO email_verify (hash, user_id)"\
                    " VALUES (%s, %s)",
                    [hash, user_id]
                )
                gmail.email_verify(email_addr, hash)
                flash('이메일을 확인하시고 인증링크를 클릭해주세요')
            flash('Register Succeeded. Please Log In.')
            return redirect(url_for('auth.login'))
        
        flash(error)
        
    return render_template('auth/register.html')

@bp.route('/business_acct_register', methods = ('GET',))
def business_acct_register():
    if g.user:
        flash("이메일 인증을 해주세요")
        return redirect(url_for('auth.account_info'))
    return render_template('auth/register.html', business_flag = True)

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if g.user:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        error = None
        user = db.select_row(
            "SELECT * FROM user_acct WHERE user_id=%s and active_flag = true", [user_id]
        )
        print('hello2')
        if user is None:
            error = 'Incorrect user id.'
        elif not check_password_hash(user['password'], password+salt):
            error = 'Incorrect password.'
        else:
            session.clear()
            session['user_id'] = user['user_id']
            ret_url = request.args.get('retUrl', '/')
            return redirect(ret_url)
        
        flash(error)
        
    return render_template('auth/login.html')
    
    
@bp.before_app_request
def load_logged_in_user():
    # model login
    if request.method=='POST' and 'user_id' in request.form and 'password' in request.form and 'required' not in request.form:
        user_id = request.form['user_id']
        password = request.form['password']
        user = db.select_row(
            "SELECT * FROM user_acct WHERE user_id=%s and active_flag = true", [user_id]
        )
        if user is None:
            flash('Incorrect user id.')
        elif not check_password_hash(user['password'], password+salt):
            flash('Incorrect password.')
        else:
            session.clear()
            session['user_id'] = user['user_id']
        return redirect(request.path)
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.select_row(
            "SELECT * FROM user_acct WHERE user_id = %s and active_flag = TRUE", [user_id]
        )
        
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
    
def admin_only(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        elif not g.user['admin_flag']:
            flash('Access denied')
            return redirect(url_for('index'))
        return view(**kwargs)
        
    return wrapped_view

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('로그인이 필요한 기능입니다.')
            return redirect(url_for('auth.login', retUrl=request.path))
        return view(**kwargs)
        
    return wrapped_view
    
def level_required(level):
    def inner_level_required(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                flash('Log in Required')
                return redirect(url_for('auth.login'))
            elif int(g.user['access_level']) > level:
                flash('Higher Access Level Required')
                return redirect(url_for('auth.account_info'))
            return view(**kwargs)
        return wrapped_view
    return inner_level_required


def change_password(new_password, user_id):
    db.update_rows(
        "UPDATE user_acct SET password = %s WHERE user_id = %s",
        [generate_password_hash(new_password+salt), user_id]
    )

@bp.route('/account', methods=('GET', 'POST'))
@login_required
def account_info():
    if request.method == 'POST':
        type = request.form['type']
        if type == 'pwd':
            cur_password = request.form['cur_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            print(cur_password, new_password, confirm_password)
            error = None
            user = db.select_row(
                "SELECT * FROM user_acct WHERE user_id=%s", [g.user['user_id']]
            )

            if not check_password_hash(user['password'], cur_password+salt):
                error = 'Incorrect password.'
            elif new_password != confirm_password:
                error = "Password didn't match"
            
            if error is None:
                change_password(new_password, g.user['user_id'])
                flash('Password Changed Successfully')
            else:
                flash(error)
        elif type == 'email':
            email_addr = request.form['email']
            if email_addr and db.select_row(
                "SELECT * FROM user_acct WHERE email = %s", [email_addr]
            ):
                flash("이미 사용중인 이메일 입니다.")
            elif email_addr:
                db.update_rows(
                    "UPDATE user_acct SET email = %s WHERE user_id = %s", [email_addr, g.user['user_id']]
                )
                hash = generate_hash(g.user['user_id'])
                db.update_rows(
                    "INSERT INTO email_verify (hash, user_id)"\
                    " VALUES (%s, %s)",
                    [hash, g.user['user_id']]
                )
                gmail.email_verify(email_addr, hash)
                flash('이메일을 확인하시고 인증링크를 클릭해주세요')
                return redirect(url_for('auth.account_info'))
            else:
                flash("이메일을 입력하세요")
        
    return render_template('auth/account.html')
    

@bp.route('/email_verify/<hash>', methods=('GET', ))
def email_verify(hash):

    res = db.select_row(
        "SELECT * FROM email_verify WHERE hash = %s AND created BETWEEN now() - interval '1 day' AND now()", [hash]
    )

    if not res:
        s = "not_valid_link"
    else:
        if res['used']:
            s = "used_veri_acct"
        else:
            db.update_rows(
                "UPDATE user_acct SET email_verified = True WHERE user_id = %s", [res['user_id']]
            )
            db.update_rows(
                "UPDATE email_verify SET used = True WHERE hash = %s", [hash]
            )
            s = "verify"
    
    return redirect(url_for('thank', s=s))
    
    
@bp.route('/find_id_pwd', methods=('GET', 'POST'))
def find_id_pwd():
    if request.method == 'POST':
        type = request.form['type']
        email_addr = request.form['email']
        if type == 'id':
            res = db.select_row(
                "SELECT * FROM user_acct WHERE active_flag = TRUE and email_verified = TRUE and email = %s", [email_addr]
            )
            if res:
                gmail.email_find_user_id(email_addr, res['user_id'])
                flash("이메일을 확인하세요.")
            else:
                flash("일치하는 이메일이 없습니다.")
        
        elif type == 'pwd':
            user_id = request.form['user_id']
            res = db.select_row(
                "SELECT * FROM user_acct WHERE active_flag = TRUE and email_verified = TRUE and user_id = %s and email = %s", [user_id, email_addr]
            )
            if res:
                tmp_password = generate_hash(user_id)[:10]
                change_password(tmp_password, user_id)
                gmail.email_tmp_password(email_addr, tmp_password)
                flash("이메일을 확인하세요.")
                return redirect(url_for('auth.login'))
            else:
                flash("일치하는 계정이 없습니다.")
                
            
    return render_template('auth/find_id_pwd.html')