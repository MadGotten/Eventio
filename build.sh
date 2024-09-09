#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install production dependecies
pip install -r production.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
