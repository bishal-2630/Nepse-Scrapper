#!/usr/bin/env bash
set -o errexit

echo "=== Starting build process ==="

# 1. Upgrade pip and tools
pip install --upgrade pip setuptools wheel

# 2. Install Cython first (helps with compilation if needed)
pip install Cython

# 3. Install numpy and pandas with binary wheels
echo "Installing numpy and pandas with pre-built wheels..."
pip install --only-binary=:all: numpy>=1.24.0 pandas>=2.2.3

# 4. Install other requirements
echo "Installing other requirements..."
pip install -r requirements.txt

python manage.py migrate --no-input
python manage.py collectstatic --no-input

# 5. Verify installations
echo "Verifying key packages..."
python -c "import django; print(f'Django {django.__version__}')"
python -c "import pandas; print(f'Pandas {pandas.__version__}')"
python -c "import celery; print(f'Celery {celery.__version__}')"

# 6. Django setup
echo "Running Django migrations..."
python manage.py migrate --no-input

echo "Collecting static files..."
python manage.py collectstatic --no-input --clear


echo "Checking if initial data setup is needed..."



echo "=== Build completed successfully ==="