#!/usr/bin/env bash
# build.sh - Render deployment script
set -o errexit

echo "=== Starting NEPSE Scraper build ==="
echo "Python version check:"
python --version

echo "Installing system dependencies..."
apt-get update -q && apt-get install -y \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    libpq-dev \
    gcc \
    build-essential \
    || echo "System dependencies installed or already present"

echo "Upgrading pip and setuptools..."
pip install --upgrade pip setuptools wheel

echo "Installing Python packages..."
pip install -r requirements.txt

echo "Running Django setup..."
python manage.py collectstatic --noinput
python manage.py migrate --noinput

echo "Verifying pandas installation..."
python -c "import pandas; print(f'pandas version: {pandas.__version__}')"

echo "=== Build complete ==="