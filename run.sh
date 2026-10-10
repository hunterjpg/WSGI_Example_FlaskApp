#! /bin/bash

set -o errexit

echo Starting Server...

source .venv/bin/activate

# EXPORTS
# See https://flask.palletsprojects.com/en/stable/config/ for info on setting via environment variables
# FLASK - Flask environment variables need to be prefixed with `FLASK_`
#export FLASK_SECRET_KEY=""
#export FLASK_RUN_PORT=443
export FLASK_MAIL_ENABLED=false
export FLASK_SERVER_NAME="$(hostname)"

# CUSTOM CONFIG
# Choose one of (CONFIG_DEFAULT, CONFIG_TESTING, CONFIG_DEBUG, CONFIG_PRODUCTION)
export CONFIG_MODE="CONFIG_PRODUCTION"

uwsgi --ini wsgi.ini