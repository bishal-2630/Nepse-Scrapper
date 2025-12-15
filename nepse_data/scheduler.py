# nepse_data/scheduler.py
import logging
from datetime import datetime
import pytz
from django.utils import timezone

logger = logging.getLogger(__name__)

# Nepal timezone
NEPAL_TZ = pytz.timezone('Asia/Kathmandu')

def scrape_daily_data():
    """
    Function to scrape daily NEPSE data.
    This will run on weekdays after market closes.
    """
    from .scrapers import NepseScraper
    from .models import DailyStockData
    
    today = timezone.now().date()
    
    # Check if today is weekday (Mon-Fri)
    if today.weekday() >= 5:  # 5=Saturday, 6=Sunday
        logger.info(f"Today is {today.strftime('%A')} - skipping scraping")
        return "Skipped (weekend)"
    
    # IMPORTANT: Check if we're scraping TODAY or a past date
    # For today, always scrape fresh data
    # For past dates, check if data already exists
    existing_count = DailyStockData.objects.filter(date=today).count()
    
    # If it's today, always scrape fresh data
    # If it's a past date and we have data, skip
    # For now, we're only scheduling today's scraping, so always scrape
    
    logger.info(f"Starting daily scraping for {today}")
    logger.info(f"Existing records for today: {existing_count}")
    
    try:
        # Delete existing data for today to ensure fresh scrape
        if existing_count > 0:
            logger.info(f"Deleting {existing_count} existing records for {today}")
            deleted_count, _ = DailyStockData.objects.filter(date=today).delete()
            logger.info(f"Deleted {deleted_count} records")
        
        # Scrape fresh data
        data = NepseScraper.scrape_today_prices()
        
        if data and len(data) > 10:
            # Save to database
            saved_count = NepseScraper.save_to_database(data)
            logger.info(f"Successfully saved {saved_count} fresh records")
            
            # Update top performers
            try:
                NepseScraper.update_top_performers(today)
                logger.info("Updated top gainers and losers")
            except Exception as e:
                logger.error(f"Failed to update top performers: {e}")
            
            return f"Scraped {saved_count} fresh records"
        else:
            logger.warning(f"No data received or insufficient data: {len(data) if data else 0} records")
            return "No data received"
            
    except Exception as e:
        logger.error(f"Error scraping data: {e}", exc_info=True)
        return f"Error: {str(e)}"

def start_scheduler():
    """Start the background scheduler"""
    try:
        # Import inside function to handle ImportError gracefully
        from apscheduler.schedulers.background import BackgroundScheduler
        from django_apscheduler.jobstores import DjangoJobStore
        from django_apscheduler import util
        from django_apscheduler.models import DjangoJobExecution
        
        # Create scheduler
        scheduler = BackgroundScheduler(timezone=NEPAL_TZ)
        
        # Use Django's job store
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # Add the job to run at 4:15 PM Nepal time every weekday
        scheduler.add_job(
            scrape_daily_data,
            trigger='cron',
            hour=16,
            minute=15,
            day_of_week='mon-fri',
            id='daily_nepse_scraping',
            max_instances=1,
            replace_existing=True,
            name='Daily NEPSE Data Scraping'
        )
        
        # Add cleanup job
        @util.retry_on_exception()
        def delete_old_job_executions(max_age=604800):
            """Delete old job execution logs"""
            DjangoJobExecution.objects.delete_old_job_executions(max_age)
        
        scheduler.add_job(
            delete_old_job_executions,
            trigger='cron',
            day_of_week='mon',
            hour=1,
            minute=0,
            id='delete_old_job_executions',
            max_instances=1,
            replace_existing=True,
            name='Clean Old Job Executions'
        )
        
        # Start the scheduler
        scheduler.start()
        logger.info("✅ NEPSE scheduler started successfully!")
        logger.info("Next scraping job scheduled for Mon-Fri at 4:15 PM Nepal Time")
        
        return scheduler
        
    except ImportError as e:
        logger.error(f"❌ Missing dependencies: {e}")
        logger.info("Install with: pip install apscheduler django-apscheduler pytz")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")
        return None