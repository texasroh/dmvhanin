from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash
from .dmvhaninlib.database import Database
from .dmvhaninlib.send_email import Gmail
from .dmvhaninlib.filestream import upload_request_file_to_s3
from .dmvhaninlib.logging import get_client_ip

import os

db = Database()
gmail = Gmail()
def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='a;slgbqgzjlxhqez;lkdghqkbzfasd',
        MAX_CONTENT_LENGTH=16*1024*1024,
    )

    @app.route("/", methods=('GET', 'POST'))
    def index():
        if request.method=='POST':
            t = request.form['type']
            if t == 'agent':
                name = request.form['name']
                company = request.form['company']
                phone = request.form['phone']
                email = request.form['email']
                div = request.form['div']
                
                db.update_rows(
                    "INSERT INTO {div} (name, company, phone, email, confirm) "\
                    "VALUES (%s, %s, %s, %s, FALSE)".format(div=div), [name, company, phone, email]
                )
                flash('반갑습니다. 등록 후 이메일 보내드리겠습니다.')
                return redirect(url_for('index'))
            elif t == 'tip':
                tip = request.form['tip']
                if tip:
                    db.update_rows(
                        "INSERT INTO tip (tip, ip_address) "\
                        "VALUES (%s, %s) ",
                        [tip, get_client_ip()]
                    )
                    flash('의견 감사합니다. 발전하는 DMV한인이 되겠습니다.')
                    return redirect(url_for('index'))
        return render_template('index.html')
        
    @app.route('/thank/<s>')
    def thank(s):
        return render_template('thank.html', s = s)
        
    @app.route('/robots.txt')
    @app.route('/sitemap.xml')
    @app.route('/naver05419653237eae21463d879e7504a4a9.html')
    @app.route('/logo.png')
    @app.route('/icon.png')
    def static_from_root():
        return send_from_directory(app.static_folder, request.path[1:])
    
    from . import auth
    app.register_blueprint(auth.bp)
    
    from . import business
    app.register_blueprint(business.bp)
    
    from . import buynsell
    app.register_blueprint(buynsell.bp)
    
    from . import board
    app.register_blueprint(board.bp)
    
    from . import admin
    app.register_blueprint(admin.bp)
    
    from . import estate
    app.register_blueprint(estate.bp)
    
    from . import car
    app.register_blueprint(car.bp)
    
    @app.route('/test', methods=('GET','POST'))
    def test():
        if request.method=='POST':
            file1 = request.files['file1']
            print(file1)
            if not file1:
                print(True)
            #upload_request_file_to_s3(file1)
            
        return render_template('test.html')
        
    '''
    @app.route('/write', methods=('GET', 'POST'))
    def write():
        if request.method=='POST':
            return str(request.form['content'])
        return render_template('write.html')
    '''
    return app
    
if __name__ == "__main__":
    create_app()