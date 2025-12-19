#!/usr/bin/env bash
# build.sh - Render deployment script
set -o errexit

echo "=== Starting NEPSE Scraper build ==="

# Remove these lines (or comment them out):
# echo "Installing system dependencies..."
# apt-get update
# apt-get install -y libxml2-dev libxslt-dev python3-dev gcc g++

# Install Python packages
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Run Django setup
echo "Running Django setup..."
python manage.py collectstatic --noinput
python manage.py migrate --noinput

echo "=== Build complete ==="