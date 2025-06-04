import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Load .env variables

class BaseConfig:
    """Base configuration (shared across environments)"""
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32))
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disables warning

class DevelopmentConfig(BaseConfig):
    """Configuration for local development (SQLite)"""
    BASE_DIR = Path(__file__).parent
    # Ensure the database directory exists
    if not (BASE_DIR / 'database').exists():
        (BASE_DIR / 'database').mkdir(parents=True)
    # Creates `dev.db` in flaskapp directory
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'database' / 'dev.db'}" 
    DEBUG = True  # Enable debug mode for development

class ProductionConfig(BaseConfig):
    """Configuration for production (PostgreSQL)"""
    DEBUG = False

    # This is not used, it is defined in docker-compose.prod.yml
    DB_USER     = os.getenv('DB_USER', 'postgres')  # Default user
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')      # Empty password if not set
    DB_HOST     = os.getenv('DB_HOST', 'db')
    DB_NAME     = os.getenv('DB_NAME', 'db_name')  # Sensible default    
    SQLALCHEMY_DATABASE_URI = (f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}")