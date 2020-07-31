from flask import Flask


def create_app():
    app = Flask(__name__)
    
    @app.route("/")
    def index():
        return "Welcome to DMV 한인"
        
    return app
    
if __name__ == "__main__":
    create_app()