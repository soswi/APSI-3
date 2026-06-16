#!/bin/bash
cd /home/site/wwwroot/backend
../antenv/bin/pip install -r requirements.txt
../antenv/bin/gunicorn apsi_3.wsgi:application --bind=0.0.0.0:8000