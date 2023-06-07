#!/bin/sh
python init_db.py
python logparser.py jupyterhub
exec "$@"