import os
from datetime import timedelta

class BaseConfig:
    """Base configuration."""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    
    # Session
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Scheduler
    SCHEDULER_API_ENABLED = True
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Server monitoring
    SERVER_MONITOR_INTERVAL = 5  # seconds

class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    DEVELOPMENT = True
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(basedir, "instance", "mydb.sqlite")
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'

class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(basedir, "instance", "test.sqlite")
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'

class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    # Use environment variables for production settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SERVER_MONITOR_INTERVAL = int(os.environ.get('SERVER_MONITOR_INTERVAL', 5))

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 