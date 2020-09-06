from flask import Flask, render_template, request
from .database import Database
from .send_email import Gmail

import os

db = Database()
gmail = Gmail()
def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='a;slgbqgzjlxhqez;lkdghqkbzfasd',
        MAX_CONTENT_LENGTH=16*1024*1024,
    )

    @app.route("/")
    def index():
        return render_template('index.html')
        
    @app.route('/thank/<s>')
    def thank(s):
        return render_template('thank.html', s = s)
        
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
    
    @app.route('/test', methods=('GET','POST'))
    def test():
        print(request)
        return request
        
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