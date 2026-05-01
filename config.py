import os
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev_key_agro_visor_9921')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database Config
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        # dj-database-url ensures compatibility with various connection strings
        # For Flask-SQLAlchemy, we ensure the protocol is 'postgresql://'
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = db_url
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///agro_visor_local.db'
    
    # Uploads
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024 # 50MB
    ALLOWED_EXTENSIONS = {'nc', 'zip'}

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # Additional production-only settings
