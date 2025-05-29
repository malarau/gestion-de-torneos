from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

login_manager = LoginManager()
db = SQLAlchemy()

# Register Blueprints
def register_blueprints(app):
    from flaskapp.modules.authentication.routes import auth_blueprint 
    from flaskapp.modules.home.routes import home_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(home_blueprint)


def create_app():
    """Create a Flask application."""
    app = Flask(__name__)               # The Flask app
    import os
    app.config['SECRET_KEY'] = os.urandom(32)
    
    # Dynamically load the config class
    env = os.getenv("FLASK_ENV", "development")  # Default: development
    if env == "production":
        app.config.from_object("flaskapp.config.ProductionConfig")
    else:
        app.config.from_object("flaskapp.config.DevelopmentConfig")
    
    db.init_app(app)                    # It instantiate the DB
    login_manager.init_app(app)         # It instantiate the login stuff

    register_blueprints(app)            # Register all routes

    with app.app_context():
        pass
        db.create_all()  # Creates tables for ALL modules' models

    return app