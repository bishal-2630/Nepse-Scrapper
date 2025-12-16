# nepse_data/apps.py
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class NepseDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nepse_data'
    
    def ready(self):
        import sys
        
        # Skip for certain commands
        skip_commands = ['makemigrations', 'migrate', 'test', 'collectstatic', 'shell']
        if any(cmd in sys.argv for cmd in skip_commands):
            return
        
        # Only start when running server
        if 'runserver' in sys.argv:
            try:
                # Start market hours scraper
                from .scheduler import start
                if start():
                    logger.info("✅ Market hours scraper started successfully!")
                    logger.info("💡 The scraper will automatically run during market hours (Mon-Fri 11:00-15:00)")
                else:
                    logger.warning("⚠️ Scraper not started")
            except ImportError as e:
                logger.error(f"❌ Missing dependencies: {e}")
            except Exception as e:
                logger.error(f"❌ Failed to start scraper: {e}")