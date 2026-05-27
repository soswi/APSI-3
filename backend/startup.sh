#!/bin/bash
python manage.py collectstatic --noinput
python manage.py migrate --noinput
gunicorn apsi_3.wsgi:application --bind=0.0.0.0:8000 --workers=2