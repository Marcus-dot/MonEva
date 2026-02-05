#!/bin/bash
cd /Users/mwelwa/DevelopmentHub/MonEva/backend
./venv/bin/python manage.py makemigrations finance > script_mig_out.txt 2>&1
./venv/bin/python manage.py migrate finance >> script_mig_out.txt 2>&1
echo "Migration finished" >> script_mig_out.txt
