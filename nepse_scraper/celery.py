import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nepse_scraper.settings')

app = Celery('nepse_scraper')

# Use PostgreSQL as broker (same as your database)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# 24/7 Scraping Schedule
app.conf.beat_schedule = {
    # Every 30 minutes, day and night
    'scrape-24x7-every-30-minutes': {
        'task': 'scrapers.tasks.scrape_24x7',
        'schedule': 1800.0,  # 30 minutes in seconds
    },
    
    # Force closing data at 3:30 PM (15:30) Nepal Time
    'force-closing-data-3-30-pm': {
        'task': 'scrapers.tasks.force_closing_data',
        'schedule': crontab(hour=15, minute=30, day_of_week='0,1,2,3,4'),  # Sun-Thu
    },
}

app.conf.timezone = 'Asia/Kathmandu'