#!/bin/sh
python manage.py update_admin_user
python manage.py runserver 0.0.0.0:8000
exec "$@"