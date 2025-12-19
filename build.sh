#!/usr/bin/env bash
# build.sh - Render deployment script
set -o errexit

echo "=== Starting NEPSE Scraper build ==="

# Install Python packages
echo "Installing Python packages..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# Run Django setup
echo "Running Django setup..."
python manage.py collectstatic --noinput
python manage.py migrate --noinput

echo "=== Build complete ==="