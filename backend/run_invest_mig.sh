#!/bin/bash
cd /Users/mwelwa/DevelopmentHub/MonEva/backend
./venv/bin/python manage.py makemigrations investigations > invest_mig.txt 2>&1
./venv/bin/python manage.py migrate investigations >> invest_mig.txt 2>&1
echo "Finished" >> invest_mig.txt
