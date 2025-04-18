#!/bin/sh
python manage.py migrate
python manage.py update_admin_user
# python manage.py create_auth_groups
python manage.py runserver 0.0.0.0:8000
exec "$@"