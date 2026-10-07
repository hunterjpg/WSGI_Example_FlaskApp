#! /bin/bash

set -o errexit

if ! command -V python3 >/dev/null; then
    echo "Error: Python not found!" 1>&2
    exit 1
fi

if [$(python3 --version) -ne 'Python 3.14.*']; then
    echo "Error: Wrong Python Version (Expected 3.14.X, got '$(echo $(python3 --version))')" 1>&2
    exit 1
fi

# See https://flask.palletsprojects.com/en/stable/config/ for info on setting via environment variables

# EXPORTS

# NGINX
#export proxy_add_x_forwarded_for=1
#export scheme=1
#export host=1

# FLASK
# Flask environment variables need to be prefixed with `FLASK_`
#export FLASK_SECRET_KEY=""
#export FLASK_RUN_PORT=443
export FLASK_MAIL_ENABLED=false
export FLASK_SERVER_NAME="$(hostname)"


# CUSTOM CONFIG
# Choose one of (CONFIG_DEFAULT, CONFIG_TESTING, CONFIG_DEBUG, CONFIG_PRODUCTION)
export CONFIG_MODE="CONFIG_PRODUCTION"

python3.14 -m venv .venv
source .venv/Scripts/activate
pip install --no-cache-dir -r requirements.txt

echo "Flask-WSGI Server is ready to use!"
