#!/bin/bash

python manage.py makemigrations --noinput --merge
python manage.py migrate

