'''Custom config parsing module\n
See https://flask.palletsprojects.com/en/stable/config/ for more information
'''

import secrets
from flask import Flask
# from flask_uploads import UploadSet
from datetime import timedelta

class DBConfig:
    '''Unused: For MySQL'''
    DB_DIALECT          = 'mysql'
    DB_SERVER           = 'localhost:port'
    DB_USER             = 'user'
    DB_PASSWORD         = 'password'
    DATABASE_PATH       = 'database'
    @property
    def DATABASE_URI(self):
        return f"{self.DB_DIALECT}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SERVER}/{self.DATABASE_PATH}"


class Config(object):
    '''Default config - Initialize by calling in app factory'''
    app_instance_path = ''
    def __init__(self, app: Flask):
        self.app_instance_path = app.instance_path
    
    # - Custom - #
    CREATE_SEED_DATA        = True
    '''Enable to seed the database with example/test data.'''
    # - App - #
    TESTING                 = False
    SECRET_KEY              = secrets.token_hex() #Placeholder
    MAX_FORM_PARTS          = 50
    MAX_FORM_MEMORY_SIZE    = 64 * 1000 * 1000
    # SERVER_NAME             = None
    LOGGING                 = True
    # - Flask-Login - #
    LOGIN_DISABLED              = False
    LOGIN_MESSAGE_CATEGORY      = 'message'
    SESSION_PROTECTION          = 'strong'
    REFRESH_MESSAGE_CATEGORY    = 'error'
    COOKIE_DURATION             = timedelta(hours=1)
    # - Run - #
    HOSTNAME        = 'localhost'
    PORT            = 8000
    DEBUG           = False
    LOAD_DOTENV     = True
    USE_RELOADER    = False
    USE_EVALEX      = False
    OPTIONS         = []
    # - Database - #
    ADMIN_USERNAME              = 'Administrator'
    ADMIN_PASSWORD              = 'changeme'
    # DB_SERVER = 'localhost'
    DATABASE_NAME               = 'site.db'
    SQLALCHEMY_DATABASE_URI     = f'sqlite+pysqlite:///{app_instance_path}/{DATABASE_NAME}'
    SQLALCHEMY_RECORD_QUERIES   = False
    SQLALCHEMY_ECHO             = False


class ProductionConfig(Config):
    '''For live use'''
    # App
    TESTING         = False
    SECRET_KEY      = 'ec862deee24a7ea40fd8b86f3ac5a4d76156016083752b1a3f190ebf48a930a6' # Placeholder
    USE_X_SENDFILE  = True # For Webservers
    # Run
    DEBUG           = False
    PORT            = 8000
    # DB
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return f'sqlite+pysqlite:///{self.app_instance_path}/{self.DATABASE_NAME}'
    SQLALCHEMY_RECORD_QUERIES   = False
    SQLALCHEMY_ECHO             = False


class DebugConfig(Config):
    '''For local unit testing and debugging'''
    # App
    TESTING         = True
    # Run
    DEBUG           = True
    USE_RELOADER    = True
    USE_EVALEX      = True
    # DB
    SQLALCHEMY_DATABASE_URI     = 'sqlite+pysqlite:///:memory:'
    SQLALCHEMY_RECORD_QUERIES   = True
    SQLALCHEMY_ECHO             = True


class DevelopmentConfig(Config):
    '''Config for local development and limited testing'''
    # App
    TESTING                     = True
    # Run
    DEBUG                       = True
    EXPLAIN_TEMPLATE_LOADING    = False
    USE_RELOADER                = True
    USE_EVALEX                  = True
    # DB
    SQLALCHEMY_DATABASE_URI     = 'sqlite+pysqlite:///:memory:'
    SQLALCHEMY_RECORD_QUERIES   = False
    SQLALCHEMY_ECHO             = False


current_config: Config


def get_current_config():
    if current_config:
        return current_config
    else:
        raise UnboundLocalError("'current_config' is unbound. Ensure that you call 'init_config' using config.")


def set_current_config(config: Config):
    current_config = config