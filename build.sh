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
    libffi-dev \
    libssl-dev \
    || echo "System dependencies installed or already present"

echo "Upgrading pip and setuptools..."
pip install --upgrade pip setuptools wheel

echo "Installing numpy first for pandas compatibility..."
pip install "numpy==1.26.4"

echo "Installing Python packages..."
pip install -r requirements.txt

echo "Running Django setup..."
python manage.py collectstatic --noinput
python manage.py migrate --noinput

echo "Verifying pandas installation..."
python -c "import pandas; print(f'pandas version: {pandas.__version__}')"
python -c "import numpy; print(f'numpy version: {numpy.__version__}')"

echo "=== Build complete ==="