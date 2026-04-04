from flask import Flask
import os

def create_app():
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    app = Flask(__name__, template_folder=template_dir)
    
    # Import and register the routes
    from app.routes import main
    app.register_blueprint(main)
    
    return app
  
