#!/usr/bin/env bash

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                                                       #
#                                           CONFIGURATION EXPORTS                                       #
#                                                                                                       #
# See https://flask.palletsprojects.com/en/stable/config/ for info on setting via environment variables #
#                   FLASK - Flask environment variables need to be prefixed with `FLASK_`               #
#                                                                                                       #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

set -e

# FLASK CONFIGS
#export FLASK_SECRET_KEY=""
#export FLASK_RUN_PORT=443
export FLASK_MAIL_ENABLED=false
export FLASK_SERVER_NAME="horseworld.ca"

# CUSTOM CONFIG
# Choose one of (CONFIG_DEFAULT, CONFIG_TESTING, CONFIG_DEBUG, CONFIG_PRODUCTION)
export CONFIG_MODE="CONFIG_PRODUCTION"
