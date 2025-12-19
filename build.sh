#!/usr/bin/env bash
# build.sh - Render deployment script
set -o errexit

echo "=== Starting NEPSE Scraper build ==="

echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Running Django setup..."
python manage.py collectstatic --noinput
python manage.py migrate --noinput

echo "=== Build complete ==="