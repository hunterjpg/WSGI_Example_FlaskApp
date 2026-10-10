#!/bin/bash

set -o errexit

if ! command -V python3 >/dev/null; then
    echo "Error: Python not found!" 1>&2
    exit 1
fi

if [[ "$(python3 --version)" =~ Python 3\.14\..*]]; then
    echo "Error: Wrong Python Version (Expected 3.14.X, got '$(echo $(python3 --version))')" 1>&2
    exit 1
fi

python3.14 -m venv .venv

source .venv/bin/activate

python -m pip install --no-cache-dir -r requirements.txt
python -m pip install pyuwsgi

echo "Flask-WSGI Server is ready to use!"
exit 0