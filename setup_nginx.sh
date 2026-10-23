#!/usr/bin/env bash

#################################################
#                                               #
# Setup script to make the environment ready    #
# Nginx Version                                 #
# Script needs to run initially as root         #
#                                               #
#################################################

#set -o errexit
set -e 

cd "$(dirname "$0")"
SRC_DIR="$(pwd)"


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
mkdir -p /var/log/flask_wsgi/ --mode=711
touch /var/log/flask_wsgi/app.log

# Selinux - Logging
semanage fcontext -a -t httpd_log_t "/var/log/flask_wsgi(/.*)?"
semanage fcontext -a -t httpd_sys_rw_content_t "/var/log/flask_wsgi(/.*)?"
restorecon -Rv /var/log/flask_wsgi

# Selinux - Static Files
semanage fcontext -a -t httpd_sys_rw_content_t "$SRC_DIR/src/static(/.*)?"
restorecon -Rv "$SRC_DIR/src/static"

# System Files
if ! [[ -e /etc/nginx/conf.d/flask_wsgi.conf ]]; then
    echo "Adding configurations to NGINX..."
    cat "$(dirname "$0")/system/nginx_proxy.conf" > /etc/nginx/conf.d/flask_wsgi.conf
    # chown nginx:nginx /etc/nginx/conf.d/nginx_proxy.conf
fi


# WSGI .ini file
if ! [[ -e $SRC_DIR/wsgi.ini ]]; then
cat > "$SRC_DIR/wsgi.ini" <<EOL
[uwsgi]
chdir = $SRC_DIR
module = wsgi:application

http-socket = 127.0.0.1:8000
# socket = /var/run/wsgi.sock
# chmod-socket = 660
vacuum = true

master = True
single-interpreter = true
processes = 2
threads = 2

uid = flask
gid = flask

die-on-term = true
harakiri = 60
harakiri-verbose = true

buffer-size = 65535
post-buffering = 65535

enable-threads = true

logto = /var/log/flask_wsgi/app.log
log-maxsize = 10485760

EOL
fi


#Init
# if ! [[ -e /etc/systemd/system/flask_wsgi.service ]]; then
#     echo -n "Creating flask_wsgi.service..."
#     cat "$(dirname "$0")/system/flask_wsgi.service" > /etc/systemd/system/flask_wsgi.service
#     systemctl daemon-reload
#     systemctl enable flask_wsgi
# fi
if ! [[ -e /etc/systemd/system/flask_wsgi.service ]]; then
cat > "/etc/systemd/system/flask_wsgi.service" <<EOL
[Unit]
Description=Flask-WSGI Webserver
After=network.target

[Service]
Type=simple
# PIDFile=/run/flask_wsgi.pid
User=flask
Group=flask
WorkingDirectory=$SRC_DIR
Environment="PATH=\$PATH:$SRC_DIR/.venv/bin"
# ExecStartPre=rm -f /run/flask_wsgi.pid
ExecStart=/usr/bin/bash $SRC_DIR/run.sh
# ExecStart=$SRC_DIR/.venv/bin/uwsgi --ini $SRC_DIR/wsgi.ini 
ExecReload=$SRC_DIR/.venv/bin/uwsgi --reload
ExecStop=$SRC_DIR/.venv/bin/uwsgi --stop --no-orphans
KillSignal=SIGQUIT
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target

EOL
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
chown -R flask:flask .
chmod 750 ./run.sh

# Done
echo "Flask-WSGI Server is ready to use!"
exit 0