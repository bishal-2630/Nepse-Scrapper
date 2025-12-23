# nepse_scrapper/celery.py
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nepse_scrapper.settings')

app = Celery('nepse_scrapper')

# For Android Termux, use memory broker
app.conf.broker_url = 'memory://'
app.conf.result_backend = 'django-db'
app.conf.broker_connection_retry_on_startup = True

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# OPTIMIZED MARKET-AWARE SCHEDULE
app.conf.beat_schedule = {
    # 1. MARKET PREPARATION (10:55 AM - Before market opens)
    'daily-market-preparation': {
        'task': 'scrapers.tasks.daily_market_opening_task',
        'schedule': crontab(hour=10, minute=55, day_of_week='sun,mon,tue,wed,thu'),
        'args': (),
    },
    
    # 2. LIVE MARKET SCRAPING (Every 5 minutes during market hours)
    'live-market-scraping': {
        'task': 'scrapers.tasks.scrape_market_data',
        'schedule': crontab(
            minute='*/5',  # Every 5 minutes
            hour='11,12,13,14',  # 11 AM to 2:59 PM
            day_of_week='sun,mon,tue,wed,thu'
        ),
        'args': (),
    },
    
    # 3. FINAL CLOSING DATA (3:30 PM - After market closes)
    'market-closing-scrape': {
        'task': 'scrapers.tasks.daily_market_closing_task',
        'schedule': crontab(hour=15, minute=30, day_of_week='sun,mon,tue,wed,thu'),
        'args': (),
    },
    
    # 4. HEALTH CHECK (Every hour, 24/7)
    'system-health-check': {
        'task': 'scrapers.tasks.health_check_task',
        'schedule': crontab(minute=0),  # Every hour at :00
        'args': (),
    },
    
    # 5. AFTER-HOURS CHECK (Every 30 minutes after market)
    'after-hours-check': {
        'task': 'scrapers.tasks.scrape_market_data',
        'schedule': crontab(
            minute='*/30',
            hour='15,16,17,18,19,20,21,22,23',  # 3 PM to 11:59 PM
            day_of_week='sun,mon,tue,wed,thu'
        ),
        'args': (),
    },
}

app.conf.timezone = 'Asia/Kathmandu'