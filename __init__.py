from flask import Flask, render_template, request, send_from_directory
from .dmvhaninlib.database import Database
from .dmvhaninlib.send_email import Gmail
from .dmvhaninlib.filestream import upload_request_file_to_s3

import os

db = Database()
gmail = Gmail()
def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='a;slgbqgzjlxhqez;lkdghqkbzfasd',
        MAX_CONTENT_LENGTH=16*1024*1024,
    )

    @app.route("/", methods=('GET', ))
    def index():
        return render_template('index.html')
        
    @app.route('/thank/<s>')
    def thank(s):
        return render_template('thank.html', s = s)
        
    @app.route('/robots.txt')
    @app.route('/sitemap.xml')
    @app.route('/naver05419653237eae21463d879e7504a4a9.html')
    @app.route('/logo.jpg')
    @app.route('/icon.jpg')
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