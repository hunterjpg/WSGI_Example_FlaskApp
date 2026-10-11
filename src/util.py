'''Some helper functions for file handling and other
'''

import os
from flask import send_from_directory, send_file, current_app
from werkzeug.utils import secure_filename
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import DateTime
from enum import Enum
from datetime import datetime, UTC
from random import randint
from markdown import Markdown #, markdown


# --- Helper Enums/Classes --- #
class PostType(Enum):
    '''Shorthands for ForumPost types'''
    ALL     = 'all'
    THREAD  = 'thread'
    REPLY   = 'reply'


class SortOrder(Enum):
    '''Default sorting order keys for database queries'''
    ALNUM   = 'alnum'
    '''Sort alphanumerically. This is a good default sorting method.'''
    CREATED = 'created'
    '''Sort by Created Date'''
    UPDATED = 'updated'
    '''Sort by most recently updated'''
    SIZE    = 'size'
    '''Size can represent file-size, reply count (for a forum thread), wordcount, etc.'''
    TAGS    = 'tags'
    '''Sort by a single tag or group of tags'''

class JinjaUtils:
    ERROR           = 'error'
    SUCCESS         = 'success'
    SORT_CREATION   = 'date'
    SORT_UPDATED    = 'updated'     # Last reply, last updated, etc.
    SORT_ALNUM      = 'alnum'
    SORT_SIZE       = 'size'        # Size can be: Filesize, reply count (i.e.: in a thread), wordcount, etc.
    SORT_TAGS       = 'tags'        # Sort by a single tag or group of tags


class Content:
    '''Util class for returning page content to a default template that can be set up to display generic data.  
    Avoids needing to make a new .html file for simple pages.  
    This is currently only used for the info pages (About, Attributions, Privacy-Policy, EULA, etc.) but is exstensible.'''
    def __init__(self, file:str|None=None, **kwargs):
        '''Accepts a file-path as a the first parameter'''
        self.title    = kwargs.get('title',     'Default Page Title')
        self.subtitle = kwargs.get('subtitle',  None)
        self.date     = kwargs.get('date',      None)
        self.sidebar  = kwargs.get('sidebar',   None)
        self.main     = kwargs.get('main',      None)
        self.xml      = kwargs.get('xml',       None)
        self.file     = kwargs.get('file',      None)


def readable_time(unix_time: int | float, timezone = UTC) -> str:
    return datetime.fromtimestamp(unix_time, timezone).strftime('%Y-%m-%d %H:%M:%S')


def ordinal(n: int):
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix

# --- UTC datetime for SQLAlchemy --- #
class utcnow(expression.FunctionElement):
    type = DateTime()
    inherit_cache = True

@compiles(utcnow, "postgresql")
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"

@compiles(utcnow, "mssql")
def ms_utcnow(element, compiler, **kw):
    return "GETUTCDATE()"

@compiles(utcnow, "mysql")
def my_utcnow(element, compiler, **kw):
    return "GETUTCDATE()"

@compiles(utcnow, "sqlite")
def sqlite_utcnow(element, compiler, **kw):
    return "unixepoch()"


# --- Files --- #
def md_to_html(directory: str, file: str) -> Content:
    '''Reads a markdown file from a `directory` (e.g.: `'static'`, `'instance'`, `'templates'`).  
    Returns a `Content` with `Content.subtitle` as the first line, and `Content.main` as 
    the rest of the markdown file in HTML.  
    _DO NOT USE USER PROVIDED FILES!_'''
    # Read markdown file by newline separated sections
    markdown: str
    _file = (uri_for(directory, filename=file))
    lines: list[str] = []
    with open(_file) as text:
        lines = text.readlines() 
    md = Markdown(extensions=['toc'])
    content = Content()
    content.title = lines.pop(0)            # First line is the title
    content.subtitle = lines.pop(0)         # Second line is the subtitle
    content.date = lines.pop(0)             # Third line is the date
    # Convert to markdown
    markdown = ''.join(lines)       
    content.main = md.convert(markdown)     # The rest of the file is the body
    content.sidebar = md.toc # type: ignore # The TOC is the sidebar
    return content


def uri_for(directory: str, filename: str) -> str:
    '''Get the full URI of a resource in the `static/`, `instance/`, or `instance/uploads/` directory via filename.  
    _DO NOT USE USER PROVIDED PATHS!_'''
    uri = ''
    match directory:
        case 'static':
            if not current_app.static_folder:
                raise FileNotFoundError('Static folder not configured')
            uri = os.path.join(current_app.static_folder, filename)
        case 'instance':
            if not os.path.exists(current_app.instance_path):
                raise FileNotFoundError('Instance folder not configured')
            uri = os.path.join(current_app.instance_path, filename)
        case 'uploads':
            if not current_app.config['UPLOAD_DIR']:
                raise FileNotFoundError('Instance or upload folder not configured')
            uri = os.path.join(current_app.config['UPLOAD_DIR'], filename)
        case _:
            raise FileNotFoundError(f"Directory '{directory}' not recognised")
    return uri


#@app.route("/uploads/<path:uri>")
def download_user_file(filename):
    '''Send a file from the user uploads directory to a client'''
    return send_from_directory(
        current_app.config['UPLOAD_DIR'], filename, as_attachment=False
    )

def download_from(filename, directory):
    '''Filepath is implicitly trusted - _DO NOT USE USER PROVIDED PATHS!_ Instead use `download_user_file`'''
    return send_file(
        directory, filename, as_attachment=False
    )

def is_allowed_file(filename: str) -> bool:
    allowed: list[str] = current_app.config['UPLOAD_ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def get_files(directory: str, prefix: str | tuple[str] = '' ) -> list | None:
    '''Gets filenames from directory non-recursively. Optionally only files with a prefix.  
    _DO NOT USE USER PROVIDED PATHS!_
    Args:
        directory (str): The directory to look in
        prefix (str | tuple[str], optional): Filename prefix to filter by. Defaults to ''.
    Returns:
        list: List of files
    '''
    filenames: list = []
    if os.path.exists(directory):
        for (dir, dirs, files) in os.walk(directory):
            if prefix:
                filenames.extend([f for f in files if f.startswith(prefix)])
            else:
                filenames.extend(files)
            break
        if not filenames:
            return None
    return filenames


def get_random_file(directory: str, prefix: str | tuple[str] = '' ) -> str | None:
    '''Gets a random filename from directory non-recursively. Optionally only files with a prefix.  
    _DO NOT USE USER PROVIDED PATHS!_
    Args:
        directory (str): The directory to look in
        prefix (str | tuple[str], optional): Filename prefix to filter by. Defaults to ''.
    Returns:
        str: Filename of a random file
    '''
    filenames = get_files(directory=directory, prefix=prefix)
    if not filenames:
        return None
    return filenames[randint(0, (len(filenames) - 1))]
