#!/bin/bash
VENV_PATH=$(find /tmp -name "activate" -path "*/antenv/*" 2>/dev/null | head -1 | sed 's|/bin/activate||')
source $VENV_PATH/bin/activate
cd /home/site/wwwroot/backend
gunicorn apsi_3.wsgi:application --bind=0.0.0.0:8000