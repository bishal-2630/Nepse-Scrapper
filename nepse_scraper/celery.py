# celery.py - UPDATED SCHEDULE
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nepse_scraper.settings')

app = Celery('nepse_scraper')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# 24/7 Scraping Schedule
app.conf.beat_schedule = {
    # 24/7 Scraping - Every 30 minutes, day and night
    'scrape-24x7-every-30-minutes': {
        'task': 'scrapers.tasks.scrape_24x7',
        'schedule': 1800.0,  # 30 minutes in seconds
        'options': {'queue': 'scraping'}
    },
    
    # Force closing data at 3:30 PM (15:30) Nepal Time - after market closes
    'force-closing-data-3-30-pm': {
        'task': 'scrapers.tasks.force_closing_data',
        'schedule': crontab(hour=15, minute=30, day_of_week='0,1,2,3,4'),  # Sun-Thu
        'options': {'queue': 'scraping'}
    },
    
    # Daily maintenance at 12:00 AM (midnight)
    'daily-maintenance-midnight': {
        'task': 'scrapers.tasks.daily_maintenance',
        'schedule': crontab(hour=0, minute=0),  # Every day at midnight
        'options': {'queue': 'maintenance'}
    },
    
    # Fill missing data on weekends (Saturday 10:00 AM)
    'fill-missing-data-weekends': {
        'task': 'scrapers.tasks.fill_missing_data',
        'schedule': crontab(hour=10, minute=0, day_of_week='6'),  # Saturday
        'options': {'queue': 'maintenance'}
    },
    
    # Backup report every Sunday
    'backup-report-sunday': {
        'task': 'scrapers.tasks.backup_historical_data',
        'schedule': crontab(hour=9, minute=0, day_of_week='0'),  # Sunday
        'options': {'queue': 'maintenance'}
    },
    
    # Quick test every hour
    'quick-test-hourly': {
        'task': 'scrapers.tasks.test_scraping_pipeline',
        'schedule': 3600.0,  # Every hour
        'options': {'queue': 'testing'}
    },
}