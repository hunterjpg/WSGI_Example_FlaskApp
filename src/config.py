'''Custom config parsing module\n
See https://flask.palletsprojects.com/en/stable/config/ for more information
'''

import os
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
    '''Enable to seed the database with an Administrator account.'''
    # - App - #
    TESTING                 = False
    SECRET_KEY              = secrets.token_hex() #Placeholder
    MAX_FORM_PARTS          = 50
    MAX_FORM_MEMORY_SIZE    = 64 * 1000 * 1000
    SERVER_NAME             = None
    LOGGING                 = True
    # - Run - #
    HOSTNAME        = 'localhost'
    PORT            = 5000
    DEBUG           = False
    LOAD_DOTENV     = True
    USE_RELOADER    = False
    USE_EVALEX      = False
    OPTIONS         = []
    # - Flask-Login - #
    LOGIN_DISABLED              = False
    LOGIN_MESSAGE_CATEGORY      = 'message'
    SESSION_PROTECTION          = 'strong'
    REFRESH_MESSAGE_CATEGORY    = 'error'
    COOKIE_DURATION             = timedelta(hours=1)
    # - Database - #
    DATABASE_NAME               = 'site.db'
    SQLALCHEMY_DATABASE_URI     = f'sqlite+pysqlite:///{app_instance_path}/{DATABASE_NAME}'
    SQLALCHEMY_RECORD_QUERIES   = False
    SQLALCHEMY_ECHO             = False


class ProductionConfig(Config):
    '''For (eventual) live use'''
    # App
    TESTING         = False
    SECRET_KEY      = 'ec862deee24a7ea40fd8b86f3ac5a4d76156016083752b1a3f190ebf48a930a6' # Placeholder
    USE_X_SENDFILE  = True # For Apache Webserver+
    # Run
    DEBUG       = False
    HOSTNAME    = '0.0.0.0'
    PORT        = 443
    # DB
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return f'sqlite+pysqlite:///{self.app_instance_path}/{self.DATABASE_NAME}'
    SQLALCHEMY_RECORD_QUERIES   = True
    SQLALCHEMY_ECHO             = False


class TestingConfig(Config):
    '''For local unit testing and debugging'''
    # App
    TESTING                     = True
    # Run
    DEBUG                       = True
    EXPLAIN_TEMPLATE_LOADING    = True
    USE_RELOADER    = True
    USE_EVALEX      = True
    # Login
    LOGIN_DISABLED              = True
    # DB
    SQLALCHEMY_DATABASE_URI     = 'sqlite+pysqlite:///:memory:'
    SQLALCHEMY_RECORD_QUERIES   = True
    SQLALCHEMY_ECHO             = False


class DevelopmentConfig(Config):
    '''Config for development and limited testing'''
    # App
    TESTING                 = True
    # Run
    DEBUG                   = True #False
    USE_RELOADER            = True
    USE_EVALEX              = True
    # DB
    SQLALCHEMY_DATABASE_URI = 'sqlite+pysqlite:///:memory:'
    SQLALCHEMY_ECHO         = False




class ConfigFile(Config):
    '''Deprecated .conf file based config'''
    from configparser import ConfigParser, Error
    # Default .conf Filename
    CFG_FILENAME = 'site.conf'
    # Config sections cases
    CFG_APP = 'app'
    CFG_DB = 'database'
    CFG_ADMIN = 'admin'
    CFG_UPLOADS = 'uploads'
    CFG_LOGIN = 'login'
    CFG_RUN = 'run'

    @property
    def CONFIG_FILE(self):
        '''FUll path to the .conf file'''
        return f'{os.path.join(self.app_instance_path, self.CFG_FILENAME)}'
    @CONFIG_FILE.setter
    def CONFIG_FILE(self, value):
        self.CONFIG_FILE = f'{os.path.join(value, self.CFG_FILENAME)}'

    def get_config(self, use_fallback: bool = False):
        if self.app_instance_path and not use_fallback:
            return os.path.join(self.app_instance_path, self.CFG_FILENAME)
        dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(dir, self.CFG_FILENAME)

    def parse_config(self, section: str) -> dict:
        '''_summary_

        Args:
            section (str): Config section to grab

        Raises:
            ValueError: On malformed section (str)

        Returns:
            dict: All entries in the requested section
        '''
        file = self.CONFIG_FILE if self.CONFIG_FILE else self.get_config(use_fallback=True)
        print(f"Config: Attempting read at '{file}'")
        try:
            if not os.path.exists(file):
                raise FileNotFoundError(f'Config: File not found. Creating {file} with values at default')
            config = self.ConfigParser()
            items = {}
            config.read(file) #config.read(CONFIG, 'utf-8')
            match section:
                # MySQL DB Config
                case 'app':
                    secret_key              = config.get(self.CFG_APP, 'SECRET_KEY',    fallback='0')
                    if not secret_key or (secret_key == '') or (secret_key == '0'):
                        items['SECRET_KEY'] = bytes(secret_key, 'utf-8')
                    else:
                        items['SECRET_KEY'] = secrets.token_hex()
                    items['TESTING']        = config.getboolean(self.CFG_APP, 'TESTING', fallback=False)

                case 'login':
                    items['SESSION_PROTECTION']         = config.get(self.CFG_LOGIN,
                                                                    'SESSION_PROTECTION',
                                                                    fallback=self.SESSION_PROTECTION)
                    items['LOGIN_MESSAGE_CATEGORY']     = config.get(self.CFG_LOGIN,
                                                                    'LOGIN_MESSAGE_CATEGORY',
                                                                    fallback=self.LOGIN_MESSAGE_CATEGORY)
                    items['REFRESH_MESSAGE_CATEGORY']   = config.get(self.CFG_LOGIN,
                                                                     'REFRESH_MESSAGE_CATEGORY',
                                                                     fallback=self.REFRESH_MESSAGE_CATEGORY)
                    items['COOKIE_DURATION']            = config.getint(self.CFG_LOGIN,
                                                                     'COOKIE_DURATION',
                                                                     fallback=self.COOKIE_DURATION)
                # Database
                case 'database':
                    items['DB_DIALECT']    = config.get(self.CFG_DB, 'DB_DIALECT',   fallback=DBConfig.DB_DIALECT)
                    items['DB_USER']       = config.get(self.CFG_DB, 'DB_USER',      fallback=DBConfig.DB_USER)
                    items['DB_PASSWORD']   = config.get(self.CFG_DB, 'DB_PASSWORD',  fallback=DBConfig.DB_PASSWORD)
                    items['DB_SERVER']     = config.get(self.CFG_DB, 'DB_SERVER',    fallback=DBConfig.DB_SERVER)
                    items['DATABASE_PATH'] = config.get(self.CFG_DB, 'DATABASE_PATH',fallback=DBConfig.DATABASE_PATH)
                    #SQLALCHEMY
                    items['SQLALCHEMY_DATABASE_URI']   = config.get(self.CFG_DB,
                                                                   'SQLALCHEMY_DATABASE_URI',
                                                                   fallback=self.SQLALCHEMY_DATABASE_URI)
                    items['SQLALCHEMY_RECORD_QUERIES'] = config.getboolean(self.CFG_DB,
                                                                    'SQLALCHEMY_RECORD_QUERIES',
                                                                    fallback=self.SQLALCHEMY_RECORD_QUERIES)
                    items['SQLALCHEMY_ECHO']           = config.getboolean(self.CFG_DB,
                                                                    'SQLALCHEMY_ECHO',
                                                                    fallback=self.SQLALCHEMY_ECHO)
                # flask.app.run() arguments
                case "run":
                    items['HOSTNAME']    = config.get(self.CFG_RUN,        'hostname', fallback=self.HOSTNAME)
                    items['PORT']        = config.getint(self.CFG_RUN,     'port',     fallback=self.PORT)
                    items['DEBUG']       = config.getboolean(self.CFG_RUN, 'debug',    fallback=self.DEBUG)
                    items['LOAD_DOTENV'] = config.getboolean(self.CFG_RUN, 'dotenv',   fallback=self.LOAD_DOTENV)
                    items['OPTIONS']     = config.get(self.CFG_RUN,        'options',  fallback=self.OPTIONS)
                # Upload Directories
                case "uploads":
                    items['UPLOAD_DIR']                 = config.get(self.CFG_UPLOADS,
                                                                        'UPLOAD_DIR',
                                                                        fallback=self.UPLOAD_DIR)
                    items['UPLOAD_ALLOWED_SIZE_MB']     = config.getint(self.CFG_UPLOADS,
                                                                        'UPLOAD_MAX_FILESIZE_MB',
                                                                        fallback=self.MAX_CONTENT_LENGTH)
                    items['UPLOAD_ALLOWED_EXTENSIONS']  = config.get(self.CFG_UPLOADS,
                                                                     'UPLOAD_ALLOWED_EXTENSIONS',
                                                                     fallback=self.UPLOAD_ALLOWED_EXTENSIONS)
                    # extensions_list = [ext.strip() for ext in extensions_raw.split(',')]
                    # items['UPLOAD_ALLOWED_EXTENSIONS'] = [ext for ext in extensions_list if ext]
                # Admin tools
                case "admin":
                    items['ADMIN_USERNAME'] = config.get(self.CFG_ADMIN, 'ADMIN_USERNAME', fallback=self.ADMIN_USERNAME)
                    items['ADMIN_PASSWORD'] = config.get(self.CFG_ADMIN, 'ADMIN_PASSWORD', fallback=self.ADMIN_PASSWORD)
                case _:
                    raise ValueError((f"Incorrect key:",
                                      f"Key was not one of '{self.CFG_APP}', '{self.CFG_DB}',", 
                                      f"'{self.CFG_UPLOADS}', '{self.CFG_LOGIN}',",
                                      f" '{self.CFG_RUN}, or '{self.CFG_ADMIN}'"))
        except self.Error as e:
            print((f"Config: '{file}' could not be read: ( ConfigParser.Error: '{str(e)}' ).",
                  f"Creating config file at '{self.get_config(use_fallback=True)}' with defaults."))
            self.create_ini_default(self.get_config(use_fallback=True))
            return self.parse_config(section)
        except FileNotFoundError as e:
            print(e)
            self.create_ini_default(file)
            return self.parse_config(section)
        else:
            return items
        finally:
            print(f"Config: Read from section '{section}'.")


    def create_ini_default(self, file_path: str = ''):
        '''Generates a default .cfg from app, app.db_config, and app.admin_config
        '''
        if not file_path:
            file_path = self.get_config(True)
        config = self.ConfigParser()
        config.add_section(self.CFG_APP)
        config.set(self.CFG_APP, 'TESTING',                str(self.TESTING))
        config.set(self.CFG_APP, 'SECRET_KEY',             self.SECRET_KEY)

        config.add_section(self.CFG_LOGIN)
        config.set(self.CFG_LOGIN, 'SESSION_PROTECTION',         self.SESSION_PROTECTION)
        config.set(self.CFG_LOGIN, 'LOGIN_MESSAGE_CATEGORY',     self.LOGIN_MESSAGE_CATEGORY)
        config.set(self.CFG_LOGIN, 'REFRESH_MESSAGE_CATEGORY',   self.REFRESH_MESSAGE_CATEGORY)
        config.set(self.CFG_LOGIN, 'COOKIE_DURATION',            str(self.COOKIE_DURATION.seconds))

        config.add_section(self.CFG_DB)
        config.set(self.CFG_DB, 'DB_USER',                   DBConfig.DB_USER)
        config.set(self.CFG_DB, 'PASSWORD',                  DBConfig.DB_PASSWORD)
        config.set(self.CFG_DB, 'DB_SERVER',                 DBConfig.DB_SERVER)
        config.set(self.CFG_DB, 'DATABASE_NAME',             self.DATABASE_NAME)
        config.set(self.CFG_DB, 'SQLALCHEMY_DATABASE_URI',   self.SQLALCHEMY_DATABASE_URI)
        config.set(self.CFG_DB, 'SQLALCHEMY_RECORD_QUERIES', str(self.SQLALCHEMY_RECORD_QUERIES))
        config.set(self.CFG_DB, 'SQLALCHEMY_ECHO',           str(self.SQLALCHEMY_ECHO))
        config.add_section(self.CFG_ADMIN)
        config.set(self.CFG_ADMIN, 'ADMIN_USERNAME',         self.ADMIN_USERNAME)
        config.set(self.CFG_ADMIN, 'ADMIN_PASSWORD',         self.ADMIN_PASSWORD)

        config.add_section(self.CFG_UPLOADS)
        config.set(self.CFG_UPLOADS, 'UPLOAD_MAX_FILESIZE_MB',       str(self.MAX_CONTENT_LENGTH))
        config.set(self.CFG_UPLOADS, 'UPLOAD_DIR',                   str(self.UPLOAD_DIR))
        config.set(self.CFG_UPLOADS, 'UPLOAD_ALLOWED_EXTENSIONS',    ','.join(self.UPLOAD_ALLOWED_EXTENSIONS))

        config.add_section(self.CFG_RUN)
        config.set(self.CFG_RUN, 'HOSTNAME',     self.HOSTNAME)
        config.set(self.CFG_RUN, 'PORT',         str(self.PORT))
        config.set(self.CFG_RUN, 'DEBUG',        str(self.DEBUG))
        config.set(self.CFG_RUN, 'LOAD_DOTENV',  str(self.LOAD_DOTENV))
        config.set(self.CFG_RUN, 'OPTIONS',      ','.join(self.OPTIONS))
        
        try:
            with open(f'{file_path}', 'w') as configfile:
                config.write(configfile)
                configfile.close()
                print(f'{file_path} created with default values')
        except Exception as e:
            print(f'Error creating {file_path}:\n\t{str(e)}\nCreating default config at:\n{self.get_config(use_fallback=True)}')
            self.create_ini_default(self.get_config(use_fallback=True))




current_config: Config


def get_current_config():
    if current_config:
        return current_config
    else:
        raise UnboundLocalError("'current_config' is unbound. Ensure that you call 'init_config' using config.")


def set_current_config(config: Config):
    current_config = config




# --- OLD STUFF --- #

# Fallback/Default config values
# admin_config = {
#     'ADMIN_USERNAME': 'admin',
#     'ADMIN_PASSWORD': 'password'
# }
# db_config = {
#     'USER':                 'root',
#     'PASSWORD':             'password', 
#     'HOST':                 'localhost',
#     'DATABASE':             'sitedb',
#     'DATABASE_URI':         'sqlite+pysqlite:///:memory:',
#     'TRACK_MODIFICATIONS':   False,
#     'ECHO':                  True,
# }
# login_config = {
#     'SESSION_PROTECTION':       'strong',
#     'LOGIN_MESSAGE_CATEGORY':   'info',
# }
# upload_config = {
#     'UPLOAD_DIR':                   '.uploads',
#     'UPLOAD_ALLOWED_EXTENSIONS':    ['gif', 'jpg', 'jpeg', 'png', 'tif', 'webp', 'avif'],
#     'UPLOAD_ALLOWED_SIZE_MB':       100
# }
# run_config = {
#     'HOSTNAME':     '127.0.0.1',
#     'PORT':         5000,
#     'DEBUG':        True,
#     'LOAD_DOTENV':  True,
#     'OPTIONS':      []
# }


# def get_config_old(section: str, key: str) -> str | int | bool | None:
#     '''Deprecated:
#         Get config key data by section and key

#     Args:
#         section (str): Config section
#         key (str): The key to retrieve data from

#     Returns:
#         str | int | bool | None: The key data, if exists (else None)
#     '''
#     return parse_config(section).get(key)


# def parse_config_old():
#     if os.path.exists(CFG_FILE):
#         config = configparser.ConfigParser()
#         try:
#             config.read(CFG_FILE) #config.read(CONFIG, 'utf-8')
#             # Course Info
#             course_info['course_title'] = config.get('course_info', 'course_title', fallback=course_info['course_title'])
#             course_info['instructor'] = config.get('course_info', 'instructor', fallback=course_info['instructor'])
#             course_info['admin_username'] = config.get('course_info', 'admin_username', fallback=course_info['admin_username'])
#             course_info['admin_password'] = config.get('course_info', 'admin_password', fallback=course_info['admin_password'])

#             # Uploads
#             #app.config['TEST_MODULE'] = config.get(section='submissions', option='test_module', fallback=TEST_MODULE)
#             app.config['ALLOWED_EXTENSIONS'] = config.get('submissions', 'allowed_extensions', fallback=UPLOAD_ALLOWED_EXTENSIONS)
#             extensions_fallback = ','.join(UPLOAD_ALLOWED_EXTENSIONS)
#             extensions_raw = config.get('submissions', 'allowed_extensions', fallback=extensions_fallback)
#             extensions_list = [ext.strip() for ext in extensions_raw.split(',')]
#             app.config['ALLOWED_EXTENSIONS'] = [ext for ext in extensions_list if ext]

#             # MySQL DB
#             db_config['user'] = config.get('mysql_db', 'user', fallback=db_config['user'])
#             db_config['password'] = config.get('mysql_db', 'password', fallback=db_config['password'])
#             db_config['host'] = config.get('mysql_db', 'host', fallback=db_config['host'])
#             db_config['database'] = config.get('mysql_db', 'database', fallback=db_config['database'])

#             # - Flask Application -
#             #Directory
#             app.config['UPLOAD_DIR'] = config.get('directory', 'upload_dir', fallback=UPLOAD_DIR)
#             app.config['TEST_DIR'] = config.get('directory', 'test_dir', fallback=TEST_DIR)

#             #Builtins
#             app.testing = config.getboolean('app', 'testing', fallback=False)
#             secret_key = config.get('app', 'secret_key', fallback='0')
#             if secret_key != '0' or '':
#                 app.secret_key = bytes(secret_key, 'utf-8')
#             else:
#                 app.secret_key = os.urandom(24)
            
#         except configparser.Error as e:
#             print(f'{CFG_FILE} could not be read: ( ConfigParser.Error: %s ). Creating {CFG_FILE} with values at default' % str(e))
#             create_ini_default()
#         else:
#             print('config applied')
#     else:
#         print(f'config file not found. Creating {CFG_FILE} with values at default')
#         create_ini_default()


# if __name__ == "__main__":
#     ConfigFile.create_ini_default()