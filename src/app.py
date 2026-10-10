'''Basic WSGI Flask-app Example
Created by Hunter M
'''

from flask import (Flask, render_template, request,
                   redirect, url_for, session, flash,
                   abort, make_response, send_from_directory)
from logging.config import dictConfig

from sqlalchemy import select
from werkzeug.exceptions import HTTPException

#from werkzeug.wsgi import
# from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

import os
from datetime import datetime#, timezone
from . import config

# ---- Testing and Debug ---- #

class WSGITestMiddleware:
    '''Custom middleware to log events for testing'''
    def __init__(self, app: Flask):
        self.app = app

    def __call__(self, environ, start_response):
        print(f"Incoming request:\n{environ['REQUEST_METHOD']:<10}\n{environ['PATH_INFO']:<10}")
        print(f"Request Remote Address:{request.remote_addr}")
        return self.app(environ, start_response)


def app_debug(_app: Flask):
    from .database import db
    with _app.app_context():
        _app.config['EXPLAIN_TEMPLATE_LOADING'] = True # Verbose template loading
        print(f"\n\nBLUEPRINTS\n{'Name':>15}{'BP':>30}{'Folder':>45}")
        for name, bp in _app.blueprints.items():
            print(f'{name:>15}\t{repr(bp):>30}{str(bp.template_folder):>45}')
        print(f'\nMain Templates: {_app.template_folder:>20}')
        print(f'\nDatabase Engine: {repr(db.get_engine()):>20}\n')
        # print(f'\nWSGI App: {_app.wsgi_app.__name__:>20}\n')

# ---- # ---- # ---- #


# ---- Logging ---- #
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})
# ---- # ---- # ---- #


# ---- Helper Functions ---- #
def dev_seed(_app: Flask):
    from .database import MetaData, db, GuestbookEntry
    '''Creates the default admin if User table is empty
    '''
    meta = db.session.query(MetaData).first()
    if meta and meta.seeded:
        return False
    if _app.config['TESTING'] or _app.config['debug']:
        try:
            if not db.session.execute(select(GuestbookEntry)).first():
                # Create 
                names = ("Worf", "J. L. Picard", "W. T. Riker", "B. Crusher", "D. Troi", "R. Barclay", "Data")
                for n in range(6):
                    t_gb = GuestbookEntry()
                    t_gb.name = names[n]
                    t_gb.message = "Hello"
                    t_gb.ip = "0.0.0.X"
                    db.session.add(t_gb)
                # Update Meta to indicate DB has been seeded
                setattr(meta, 'seeded', True)
                db.session.commit()
                return True
        except Exception as e:
            db.session.rollback()
            raise Exception from e
    return False


def setup_dirs(_app: Flask):
    try:
        os.makedirs(_app.instance_path)
    except OSError:
        print(f"Instance directory at {_app.instance_path} already exists or was inaccessible!")


# ---- APP INITS ---- #
def init_config(_app: Flask): #-> Config
    '''Initialise a custom config and apply the configuration to the app.'''
    config_mode = os.getenv('CONFIG_MODE')
    if config_mode:
        match config_mode:
            case 'CONFIG_DEFAULT':
                config.current_config = config.Config(_app)
            case 'CONFIG_TESTING':
                config.current_config = config.DebugConfig(_app)
            case 'CONFIG_DEBUG':
                config.current_config = config.DevelopmentConfig(_app)
            case 'CONFIG_PRODUCTION':
                config.current_config = config.ProductionConfig(_app)
            case _:
                config.current_config = config.DevelopmentConfig(_app)
    else:
        print("DEBUG: No 'CONFIG_MODE' environment variable defined. Defaulting to DebugConfig")
        config.current_config = config.DebugConfig(_app)
    # Apply the config from the config object first
    _app.config.from_object(config.current_config)
    # Then apply any envvar overrides
    _app.config.from_prefixed_env()


def init_db(_app: Flask): #-> SQLAlchemy:
    '''Init SQLAlchemy: Connect app and create tables.  
    Also sets up MetaData'''
    with _app.app_context():
        from .database import MetaData, db
        db.init_app(_app)
        db.create_all()
        # Meta Entry
        meta = MetaData()
        MetaData.setup_meta(meta)
        if _app.config['CREATE_SEED_DATA']:
            dev_seed(_app)


def init_csrf(_app: Flask): #-> CSRFProtect:
    '''Init CSRF protection for FlaskForms/Flask-WTF'''
    with _app.app_context():
        from .forms import csrf
        csrf.init_app(_app)


def init_wsgi (_app: Flask):
    _app.wsgi_app = ProxyFix(
        _app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_prefix=1
    )


# Flask Application
def create_app() -> Flask:
    _app = Flask(__name__)
    ## Apply .conf file
    init_config(_app)
    # Create DB Dirs
    setup_dirs(_app)
    # Register blueprints
    from . import routes
    _app.register_blueprint(routes.bp)
    # Inits
    init_db(_app)
    init_csrf(_app)
    # Debug/Testing
    if _app.config['DEBUG']:
        app_debug(_app)
    elif _app.config['TESTING']:
        _app.wsgi_app = WSGITestMiddleware(_app) #TEST WSGI
        # init_wsgi(_app)
    elif _app.config['PRODUCTION']:
        init_wsgi(_app)
    # Jinja2 Extensions
    _app.jinja_env.add_extension('jinja2.ext.loopcontrols')
    return _app

app: Flask = create_app()


# ---- Global Routes ---- #
@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:]) # type: ignore


@app.route('/toggle_theme')
def toggle_theme():
    curr_theme = session.get('theme')
    if curr_theme == 'dark':
        session['theme'] = 'light'
    else:
        session['theme'] = 'dark'
    return redirect(request.referrer)


@app.route('/redirect?ref=<string:ref>')
def redirect_to(ref: str = ''):
    '''Redirects to a URL `ref`, or the `request.path` URL if `ref` is not provided.'''
    if not ref:
        ref = request.path
    return redirect(ref)


@app.route('/redirect/')
def redir():
    return redirect(url_for('index'))


@app.route('/health/', websocket=True,  methods=['GET', 'HEAD'])
def health():
    #TODO: make a better WSOCK route for remote health checking that returns some basic data (uptime, server load, disk stats, etc)
    # Maybe move this to `api`
    return 'OK', 200


# @app.get('/dev/seed')
# def dev_seed_route():
#     from flask import render_template_string
#     if dev_seed():
#         admin_name   = config.current_config.ADMIN_USERNAME
#         admin_email  = config.current_config.ADMIN_EMAIL
#         temp = (f'<h1>Created Seed Admin</h1>'
#                 f"<p>Username: '{admin_name}'</p>"
#                 f'<p>Email: {admin_email}</p>')
#         return render_template_string(temp), 200
#     return abort(404)
# ---- # ---- # ---- #


# ---- Standard HTTP Error Handlers ---- #
def get_error_image(code: int):
    from .util import get_random_file
    image = get_random_file(directory=f'{app.static_folder}/img/errors/', prefix=str(code))
    if not image:
        image = get_random_file(directory=f'{app.static_folder}/img/errors/', prefix='500')
    return url_for('static', filename=f'img/errors/{image}')

@app.get('/teapot/')
def teapot():
    abort(418, "I'm a teapot!")

@app.errorhandler(418)
def im_a_teapot(e):
    '''I'm a teapot. The body may be short and/or stout.'''
    image = get_error_image(418)
    if request.path.startswith('/api') or '/api' in request.path:
        from flask import jsonify
        return jsonify(message=e.name, data=image), 418
    return make_response(render_template('base_error.html', random_image=image, error=e), 418)


@app.errorhandler(503)
def service_unavailable(e, retry_after: datetime | int | None = 3600):
    '''Service Unavailable.'''
    # title = '503: Service Unavailable'
    e.retry_after = retry_after
    if request.path.startswith('/api') or '/api/' in request.path:
        from flask import jsonify
        return jsonify(message=e.name, retry_after=retry_after), 503
    image = get_error_image(503)
    response = make_response(render_template('base_error.html',
                                             random_image=image,
                                             error=e), 
                                            503)
    response.retry_after = retry_after
    return response


@app.errorhandler(HTTPException)
def handle_error(e):
    '''Catchall error handler'''
    if request.path.startswith('/test/error'):
        print(f'ErrorObj:\n\t{e}')
        print(f'Name:\n\t{e.name}')
        print(f'Code:\n\t{e.code}')
        print(f'Desc.:\n\t{e.description}')
        print(f'CurrentPage:\n\t{request.path}')
    if request.path.startswith('/api') or '/api/' in request.path:
        from flask import jsonify
        return jsonify(message=e.name), e.code
    image = get_error_image(e.code)
    response = make_response(render_template('base_error.html', random_image=image, error=e), e.code)
    return response
