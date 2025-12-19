#!/usr/bin/env bash
# build.sh - Render deployment script

echo "=== Starting NEPSE Scraper build ==="

# Install dependencies
pip install --only-binary :all: --find-links https://wheels.grahamw.net/simple/ -r requirements.txt

# Apply database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Run initial setup (scraping)
echo "Running initial setup..."
python render_init.py

echo "=== Build complete ==="