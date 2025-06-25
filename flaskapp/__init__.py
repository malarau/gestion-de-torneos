from flask import Flask, render_template
from flask_login import LoginManager
from flaskapp.database.models import db
import os

login_manager = LoginManager()

# Register Blueprints
def register_blueprints(app):
    from flaskapp.modules.authentication.routes import auth_blueprint 
    from flaskapp.modules.home.routes import home_blueprint
    from flaskapp.modules.organizations.routes import org_bp
    from flaskapp.modules.profile.routes import profile_blueprint
    from flaskapp.modules.activities.routes import activities_blueprint
    from flaskapp.modules.events.routes import events_bp
    from flaskapp.modules.tournaments.routes import tournaments_bp
    from flaskapp.modules.teams.routes import teams_bp
    from flaskapp.modules.matches.routes import matches_bp
    from flaskapp.modules.notifications.routes import notifications_bp

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(home_blueprint)
    app.register_blueprint(org_bp)
    app.register_blueprint(profile_blueprint)
    app.register_blueprint(activities_blueprint)
    app.register_blueprint(events_bp)
    app.register_blueprint(tournaments_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(matches_bp)
    app.register_blueprint(notifications_bp)

    # Add global blueprints as needed
    @app.errorhandler(403)
    def access_forbidden(error, msg=None):
        return render_template('home/page-403.html', msg=msg), 403
    @app.errorhandler(404)
    def not_found_error(error, msg=None):
        return render_template('home/page-404.html', msg=msg), 404
    @app.errorhandler(500)
    def internal_error(error, msg=None):
        return render_template('home/page-500.html', msg=msg), 500

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