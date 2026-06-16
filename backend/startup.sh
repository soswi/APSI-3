#!/bin/bash
cd /home/site/wwwroot

# Rozpakuj antenv jeśli nie jest jeszcze rozpakowany
if [ ! -f antenv/lib/python3.11/site-packages/django/__init__.py ]; then
    echo "Rozpakowywanie antenv.tar.gz..."
    tar -xzf antenv.tar.gz
fi

antenv/bin/gunicorn apsi_3.wsgi:application --bind=0.0.0.0:8000