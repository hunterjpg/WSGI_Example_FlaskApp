#!/usr/bin/env bash

#################################################
#                                               #
# Setup script to make the environment ready    #
# Script needs to run initially as root         #
#                                               #
#################################################

#set -o errexit
set -e 

cd "$(dirname "$0")"

# Checks
if ! command -V nginx >/dev/null; then
    echo -n "Error: NGINX not found! " 1>&2
    echo "Please install nginx."
    exit 1
fi

if ! command -V python3 >/dev/null; then
    echo "Error: Python not found!" 1>&2
    exit 1
fi

if ! [[ "$(python3 --version)" =~ Python 3\.14\..*]]; then
    echo "Error: Wrong Python Version (Expected 3.14.X, got '$(echo $(python3 --version))')" 1>&2
    exit 1
fi

# User Setup
useradd flask -s /bin/bash --system
usermod flask -aG nginx

# Log Setup
echo -n "Setting up logging..."
mkdir -p /var/log/nginx/flask/ --mode=711
touch /var/log/flask_wsgi/app.log
touch /var/log/flask_wsgi/access.log
touch /var/log/flask_wsgi/error.log
# Selinux - Logging
semanage fcontext -a -t httpd_log_t "/var/log/flask_wsgi(/.*)?"
restorecon -Rv /var/log/flask_wsgi

# Selinux - Static Files
semanage fcontext -a -t httpd_sys_rw_content_t "/var/www/flask_wsgi/src/static(/.*)?"
restorecon -Rv /var/www/flask_wsgi/src/static

# System Files
if ! [[ -e /etc/nginx/conf.d/flask_wsgi.conf ]]; then
    echo "Adding configurations to NGINX..."
    cat "$(dirname "$0")/system/nginx_proxy.conf" > /etc/nginx/conf.d/flask_wsgi.conf
    # chown nginx:nginx /etc/nginx/conf.d/nginx_proxy.conf
fi

if ! [[ -e /etc/systemd/system/flask_wsgi.service ]]; then
    echo -n "Creating flask_wsgi.service..."
    cat "$(dirname "$0")/system/flask_wsgi.service" > /etc/systemd/system/flask_wsgi.service
    systemctl daemon-reload
    systemctl enable flask_wsgi
fi

# Python Setup
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --no-cache-dir -r requirements.txt
# pip install --no-binary pyuwsgi pyuwsgi
python -m pip install pyuwsgi 

# Misc
chmod 750 ./run.sh

# Done
echo "Flask-WSGI Server is ready to use!"
exit 0