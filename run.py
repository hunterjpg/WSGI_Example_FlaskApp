'''Run some basic setup then run the app.'''
from src import app as appsrc
import os
from src.modules.config import current_config
from src.app import create_default_admin


def setup_dirs():
    try:
        os.makedirs(current_config.UPLOAD_DIR)
    except OSError:
        print(f"Upload directory at {current_config.UPLOAD_DIR} already exists or was inaccessible!")
    try:
        os.makedirs(appsrc.app.instance_path)
    except OSError:
        print(f"Instance directory at {appsrc.app.instance_path} already exists or was inaccessible!")


if __name__ == "__main__":
    setup_dirs()
    appsrc.app.run() #Do not use app.run on production! Need WSGI server.