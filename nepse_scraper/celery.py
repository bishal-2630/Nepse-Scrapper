import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nepse_scraper.settings')

app = Celery('nepse_scraper')

# For Android Termux, use memory broker
app.conf.broker_url = 'memory://'
app.conf.result_backend = 'django-db'
app.conf.broker_connection_retry_on_startup = True

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Optimized schedule for Android
app.conf.beat_schedule = {
    # Every 30 minutes, 24/7
    'scrape-24x7-every-30-minutes': {
        'task': 'scrapers.tasks.scrape_24x7',
        'schedule': 1800.0,  # 30 minutes in seconds
    },
    
    # Force closing data at 3:30 PM Nepal Time (Sunday-Thursday)
    'force-closing-data-3-30-pm': {
        'task': 'scrapers.tasks.force_closing_data',
        'schedule': crontab(hour=15, minute=30, day_of_week='0,1,2,3,4'),
    },
    
    # Daily maintenance at 4 PM
    'daily-maintenance': {
        'task': 'scrapers.tasks.daily_maintenance',
        'schedule': crontab(hour=16, minute=0),
    },
}

app.conf.timezone = 'Asia/Kathmandu'