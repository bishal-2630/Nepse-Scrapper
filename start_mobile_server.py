#!/usr/bin/env python
"""
Mobile server startup script for Android
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if all required packages are installed"""
    required = ['Django', 'celery', 'django-celery-beat']
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    return missing

def setup_environment():
    """Setup environment for Android"""
    # Set environment variables
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nepse_scraper.settings')
    
    # Create necessary directories
    dirs = ['staticfiles', 'logs', 'backups', 'media']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    
    # Android-specific setup
    if 'com.termux' in os.environ.get('PREFIX', ''):
        print("📱 Android/Termux environment detected")
        
        # Setup shared storage symlink
        shared_storage = Path('/data/data/com.termux/files/home/storage/shared/NEPSE-Server')
        if shared_storage.exists():
            # Create symlink to shared storage for backups
            backups_dir = shared_storage / 'backups'
            backups_dir.mkdir(exist_ok=True)
            
            if not Path('backups').exists():
                os.symlink(backups_dir, 'backups')

def start_services():
    """Start all required services"""
    print("🚀 Starting NEPSE Mobile Server...")
    
    processes = []
    
    # 1. Apply migrations
    print("📦 Applying database migrations...")
    subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
    
    # 2. Collect static files
    print("📁 Collecting static files...")
    subprocess.run([sys.executable, 'manage.py', 'collectstatic', '--noinput'], check=True)
    
    # 3. Start Celery worker (if Redis is available)
    try:
        print("🔄 Starting Celery worker...")
        celery_proc = subprocess.Popen([
            sys.executable, '-m', 'celery',
            '-A', 'nepse_scraper',
            'worker',
            '--loglevel=info',
            '--concurrency=1'  # Single worker for mobile
        ])
        processes.append(celery_proc)
        print("✅ Celery worker started")
    except Exception as e:
        print(f"⚠️  Celery worker failed: {e}")
    
    # 4. Start Celery beat
    try:
        print("⏰ Starting Celery beat...")
        beat_proc = subprocess.Popen([
            sys.executable, '-m', 'celery',
            '-A', 'nepse_scraper',
            'beat',
            '--loglevel=info'
        ])
        processes.append(beat_proc)
        print("✅ Celery beat started")
    except Exception as e:
        print(f"⚠️  Celery beat failed: {e}")
    
    # 5. Start Django development server
    print("🌐 Starting Django server...")
    django_proc = subprocess.Popen([
        sys.executable, 'manage.py', 'runserver',
        '0.0.0.0:8000',
        '--noreload',  # Disable reload for mobile
        '--nothreading'  # Single thread for mobile
    ])
    processes.append(django_proc)
    
    print("\n" + "="*50)
    print("✅ NEPSE Mobile Server Started Successfully!")
    print("="*50)
    print("\n📊 Access URLs:")
    print("   Local:      http://localhost:8000")
    print("   Network:    http://<your-ip>:8000")
    print("\n📱 API Endpoints:")
    print("   /api/status/              - Market status")
    print("   /api/stocks/latest/       - Latest stock data")
    print("   /api/stocks/top-gainers/  - Top gainers")
    print("   /api/stocks/top-losers/   - Top losers")
    print("   /health/                  - Health check")
    print("\n💡 Tips:")
    print("   • Use ngrok for public access: ./ngrok http 8000")
    print("   • Keep phone plugged in for 24/7 operation")
    print("   • Disable battery optimization for Termux")
    print("="*50)
    
    # Keep script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        for proc in processes:
            proc.terminate()
        print("✅ Server stopped")

if __name__ == '__main__':
    # Add project to Python path
    project_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_root))
    
    # Setup
    setup_environment()
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Start services
    start_services()