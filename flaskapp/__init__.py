from flask import Flask
from flask_login import LoginManager
from flaskapp.database.models import db
import os

login_manager = LoginManager()

# Register Blueprints
def register_blueprints(app):
    from flaskapp.modules.authentication.routes import auth_blueprint 
    from flaskapp.modules.home.routes import home_blueprint
    from flaskapp.modules.organizations.routes import org_bp

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(home_blueprint)
    app.register_blueprint(org_bp)

def create_app():
    """Create a Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.urandom(32)
    
    # Dynamically load the config class
    env = os.getenv("FLASK_ENV", "development")  # Default: development
    if env == "production":
        app.config.from_object("flaskapp.config.ProductionConfig")
    else:
        app.config.from_object("flaskapp.config.DevelopmentConfig")
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Import models to ensure they're registered with SQLAlchemy
    from flaskapp.database import models
    
    # Import authentication loaders
    from flaskapp.database import auth_loaders
    
    # Register blueprints
    register_blueprints(app)
    
    # Create database tables and seed data
    with app.app_context():
        db.create_all()   # Creates tables for ALL modules' models
        #seed_base_data()  # Insert base data required for system operation
    
        # Seed the database with test data
        seed_db_command(app)

    return app

def seed_db_command(app):
    """
    Puebla la base de datos con datos de prueba.
    Crea usuarios, organizaciones, torneos, equipos, etc.
    """
    from .database.seeder import seed_database
    
    seed_database(app)
    

def seed_base_data():
    """Seed base data required for system operation."""
    from sqlalchemy import text
    
    try:
        # Check if base data already exists
        result = db.session.execute(text("SELECT COUNT(*) FROM event_statuses")).scalar()
        
        if result == 0:  # Only seed if tables are empty
            # Read and execute base data seed file
            base_data_path = os.path.join(
                os.path.dirname(__file__), 
                'database', 
                'seed_base_data.sql'
            )
            
            if os.path.exists(base_data_path):
                with open(base_data_path, 'r', encoding='utf-8') as f:
                    sql_commands = f.read()
                    
                db.session.execute(text(sql_commands))                
                db.session.commit()
                print("Base data seeded successfully")
            else:
                print(f"Seed file not found: {base_data_path}")
                
    except Exception as e:
        print(f"Error seeding base data: {e}")
        db.session.rollback()