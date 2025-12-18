web: gunicorn nepse_scraper.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A nepse_scraper worker --loglevel=info
beat: celery -A nepse_scraper beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
