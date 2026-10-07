#! /bin/bash

set -o errexit


echo Starting Server...


uwsgi --ini wsgi.ini