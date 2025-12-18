#!/usr/bin/env bash
# build.sh - Render deployment script

echo "=== Starting NEPSE Scraper build ==="

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate --noinput

echo "=== Build complete ==="