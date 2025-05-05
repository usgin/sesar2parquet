#!/bin/sh

# Apply database migrations
python manage.py migrate

# Custom Django admin setup
python manage.py update_admin_user
python manage.py create_auth_groups

# Start Gunicorn WSGI server
exec gunicorn sesar.wsgi:application --bind 0.0.0.0:8000 --workers 3