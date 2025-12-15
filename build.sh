#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Fix: Reinstall setuptools to ensure pkg_resources is available
pip install --force-reinstall -U setuptools

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate