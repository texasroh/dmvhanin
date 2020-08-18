from flask import Flask, render_template
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
        
    return app
    
if __name__ == "__main__":
    create_app()