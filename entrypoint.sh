#!/bin/sh
python manage.py makemigrations
python manage.py migrate
python init_db.py
python logparser.py jupyterhub
exec "$@"