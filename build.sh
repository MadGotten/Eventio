#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install production dependencies
pip install -r production.txt

# Move to django project app
cd Eventio

# Install node modules dependencies
npm install

# Minify tailwindcss
npm run build

# Convert static asset files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
