#!/bin/bash
# Android Termux NEPSE Server Startup Script

echo "======================================="
echo "  NEPSE Scraper Server for Android"
echo "======================================="

# Check if we're in Termux
if [ ! -d "/data/data/com.termux/files/home" ]; then
    echo "Warning: This script is designed for Termux on Android"
fi

echo "1. Activating Python environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "   Virtual environment activated"
else
    echo "   No virtual environment found, using system Python"
fi

echo "2. Installing requirements..."
pip install -r requirements.txt > /dev/null 2>&1
echo "   Requirements installed"

echo "3. Setting up database..."
python manage.py migrate
echo "   Database migrations completed"

echo "4. Creating admin user if not exists..."
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("   Admin user created (admin/admin123)")
else:
    print("   Admin user already exists")
EOF

echo "5. Starting Celery Beat (scheduler)..."
celery -A nepse_scraper beat --loglevel=info --detach
echo "   Celery Beat started"

echo "6. Starting Celery Worker..."
celery -A nepse_scraper worker --loglevel=info --detach
echo "   Celery Worker started"

echo "7. Starting Django development server..."
echo "======================================="
echo "  Server is starting on 0.0.0.0:8000"
echo "  Press Ctrl+C to stop"
echo "======================================="
echo ""
echo "Access URLs:"
echo "  - Local: http://localhost:8000"
echo "  - Network: http://YOUR_IP:8000"
echo "  - API Docs: http://localhost:8000/swagger/"
echo "  - Admin: http://localhost:8000/admin/"
echo ""
echo "To expose publicly, run in another terminal:"
echo "  ngrok http 8000"
echo "======================================="

python manage.py runserver 0.0.0.0:8000