#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install production dependecies
pip install -r production.txt

# Move to django project app
cd Eventio

# Convert static asset files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
