#!/usr/bin/env bash

#################################################
#                                               #
#               Startup Script                  #
#      Script will be run by flask.service      #
#                                               #
#################################################

#set -o errexit
set -e 

echo -n "Starting Server..."

cd "$(dirname "$0")"

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

/var/www/flask_uwsgi/.venv/bin/uwsgi --ini wsgi.ini 1>/dev/null 2>>/var/log/flask_uwsgi/error.log

echo -n "Server Started..."
