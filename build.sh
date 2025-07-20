#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install uv
pip install uv

# Install production dependencies
uv sync --locked

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
