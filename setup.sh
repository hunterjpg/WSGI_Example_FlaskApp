#!/bin/bash

#################################################
#                                               #
# Setup script to make the environment ready    #
# Script needs to run initially as root         #
#                                               #
#################################################

set -o errexit

cd "$(dirname "$0")"

# Checks
if ! command -V nginx >/dev/null; then
    echo -n "Error: NGINX not found!" 1>&2
    echo "Install package 'nginx'."
    exit 1
fi

if ! command -V python3 >/dev/null; then
    echo -n "Error: Python not found!" 1>&2
    exit 1
fi

if ! [[ "$(python3 --version)" =~ Python 3\.14\..*]]; then
    echo -n "Error: Wrong Python Version (Expected 3.14.X, got '$(echo $(python3 --version))')" 1>&2
    exit 1
fi

# User Setup
useradd flask -s /bin/bash --system

# Dir Setup
echo -n "Setting up directories..."
mkdir -p /var/log/nginx/flask/ --mode=711
touch /var/log/nginx/flask/app.log
touch /var/log/nginx/flask/access.log
touch /var/log/nginx/flask/error.log

# System Files
if ! [[ -e /etc/nginx/conf.d/nginx_proxy.conf ]]; then
    echo -n "Adding configurations to NGINX..."
    cat ./system/nginx_proxy.conf > /etc/nginx/conf.d/nginx_proxy.conf
    # chown nginx:nginx /etc/nginx/conf.d/nginx_proxy.conf
fi

if ! [[ -e /etc/systemd/system/flask.service ]]; then
    echo -n "Creating flask.service..."
    cat ./system/flask.service > /etc/systemd/system/flask.service
    systemctl daemon-reload
    systemctl enable flask
fi

# Python Setup
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --no-cache-dir -r requirements.txt
python -m pip install pyuwsgi

# Misc
chmod 750 ./run.sh

# Done
echo -n "Flask-WSGI Server is ready to use!"
exit 0