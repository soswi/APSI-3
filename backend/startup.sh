#!/bin/bash
cd /home/site/wwwroot
antenv/bin/pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
antenv/bin/gunicorn apsi_3.wsgi:application --bind=0.0.0.0:8000