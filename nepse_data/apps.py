# nepse_data/apps.py
from django.apps import AppConfig
import sys
import os

class NepseDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nepse_data'
    
    def ready(self):
        # Skip for migration commands and shell
        skip_for = ['makemigrations', 'migrate', 'shell', 'test', 'createsuperuser', 'collectstatic']
        
        if any(cmd in sys.argv for cmd in skip_for):
            return
        
        # Only start when running server
        if 'runserver' in sys.argv:
            # Check if we're in the auto-reloader child process
            if os.environ.get('RUN_MAIN') or not os.environ.get('DJANGO_AUTORELOAD'):
                try:
                    from .scheduler import start_scheduler
                    scheduler = start_scheduler()
                    if scheduler:
                        print("✅ NEPSE data scheduler initialized successfully")
                    else:
                        print("⚠️ Scheduler not started (check logs)")
                except ImportError as e:
                    print(f"⚠️ Scheduler module not available: {e}")
                    print("Install with: pip install apscheduler django-apscheduler pytz")
                except Exception as e:
                    print(f"⚠️ Could not start scheduler: {e}")