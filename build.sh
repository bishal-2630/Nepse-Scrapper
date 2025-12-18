

echo "=== Starting NEPSE Scraper build ==="

# Set Python path
export PYTHONPATH=/opt/render/project/src:$PYTHONPATH

# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install dependencies one by one to identify any issues
echo "Installing core dependencies..."
pip install Django==4.2.7
pip install djangorestframework==3.14.0
pip install drf-yasg==1.21.7
pip install celery==5.3.4
pip install django-celery-beat==2.5.0
pip install django-celery-results==2.5.0
pip install requests==2.31.0
pip install beautifulsoup4==4.12.2

# Install lxml with system dependencies
apt-get update && apt-get install -y libxml2-dev libxslt-dev python3-dev
pip install lxml==4.9.3


pip install pandas==2.2.2

# Install remaining dependencies
pip install python-dotenv==1.0.0
pip install psycopg2-binary==2.9.9
pip install gunicorn==21.2.0
pip install django-cors-headers==4.3.0
pip install whitenoise==6.6.0
pip install dj-database-url==2.1.0



# Apply database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

echo "=== Build complete ==="