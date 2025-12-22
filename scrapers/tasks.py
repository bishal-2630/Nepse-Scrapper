# scrapers/tasks.py - COMPLETELY UPDATED FOR RELIABLE AUTOMATIC SCRAPING
from celery import shared_task
from celery.schedules import crontab
from django.utils import timezone
from django.db.models import Max
from datetime import datetime, timedelta, time as time_obj
import logging
import pytz
from .data_processor import NepseDataProcessor24x7
from .models import MarketStatus

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def scrape_market_data(self):
    """
    MAIN TASK: Scrape NEPSE data with market-aware scheduling
    Runs every 5 minutes during market hours, stops after market closes
    """
    nepal_tz = pytz.timezone('Asia/Kathmandu')
    now = timezone.now().astimezone(nepal_tz)
    today = now.date()
    current_time = now.time()
    
    # Get or create market status
    market_status, created = MarketStatus.objects.get_or_create(
        date=today,
        defaults={
            'is_market_open': False,
            'last_scraped': None,
            'total_turnover': 0,
            'total_volume': 0,
            'total_transactions': 0
        }
    )
    
    # Check if market should be open
    is_market_hours = _is_market_open_now(now)
    market_status.is_market_open = is_market_hours
    market_status.last_scraped = now
    
    # If market closed and we already have closing data, skip
    if not is_market_hours:
        # Check if we already have closing data for today
        from .models import StockData
        has_closing_data = StockData.objects.filter(
            scrape_date=today,
            is_closing_data=True
        ).exists()
        
        if has_closing_data:
            logger.info(f"Market closed and closing data already exists for {today}. Skipping.")
            market_status.save()
            return {
                'status': 'skipped',
                'reason': 'Market closed with existing closing data',
                'date': str(today),
                'time': str(current_time)
            }
    
    try:
        # Run the scraper
        processor = NepseDataProcessor24x7()
        result = processor.execute_scraping()
        
        # Update market status with scrape results
        if result.get('success'):
            records_saved = result.get('records_saved', 0)
            logger.info(f"✅ Successfully scraped {records_saved} records for {today} {current_time}")
            
            # Update market stats if available
            if 'total_turnover' in result:
                market_status.total_turnover = result.get('total_turnover', 0)
                market_status.total_volume = result.get('total_volume', 0)
                market_status.total_transactions = result.get('total_transactions', 0)
        
        market_status.save()
        
        # If this is closing time, mark as closing data
        if _is_closing_time(now):
            _mark_todays_data_as_closing(today)
        
        return {
            'status': 'success',
            'records_saved': result.get('records_saved', 0),
            'date': str(today),
            'time': str(current_time),
            'market_open': is_market_hours
        }
        
    except Exception as e:
        logger.error(f"❌ Scraping failed: {e}", exc_info=True)
        
        # Retry logic
        try:
            self.retry(countdown=60, max_retries=3)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for {today}")
        
        return {
            'status': 'error',
            'error': str(e),
            'date': str(today),
            'time': str(current_time)
        }

@shared_task
def daily_market_opening_task():
    """
    Run at 10:55 AM daily to prepare for market opening
    """
    nepal_tz = pytz.timezone('Asia/Kathmandu')
    now = timezone.now().astimezone(nepal_tz)
    today = now.date()
    
    logger.info(f"⏰ Daily market opening preparation for {today}")
    
    # Ensure market status exists
    MarketStatus.objects.get_or_create(
        date=today,
        defaults={
            'is_market_open': False,
            'last_scraped': None,
            'total_turnover': 0,
            'total_volume': 0,
            'total_transactions': 0
        }
    )
    
    return {'status': 'ready', 'date': str(today)}

@shared_task
def daily_market_closing_task():
    """
    Run at 3:30 PM daily to capture final closing data
    """
    nepal_tz = pytz.timezone('Asia/Kathmandu')
    now = timezone.now().astimezone(nepal_tz)
    today = now.date()
    
    logger.info(f"🏁 Daily market closing task for {today}")
    
    # Force a final scrape
    processor = NepseDataProcessor24x7()
    result = processor.execute_scraping()
    
    # Mark all today's data as closing data
    records_marked = _mark_todays_data_as_closing(today)
    
    # Update market status to closed
    try:
        market_status = MarketStatus.objects.get(date=today)
        market_status.is_market_open = False
        market_status.last_scraped = now
        market_status.save()
    except MarketStatus.DoesNotExist:
        pass
    
    return {
        'status': 'closing_complete',
        'records_marked': records_marked,
        'date': str(today)
    }

@shared_task
def health_check_task():
    """
    Health check - runs every hour to ensure system is alive
    """
    from .models import StockData, Company
    
    nepal_tz = pytz.timezone('Asia/Kathmandu')
    now = timezone.now().astimezone(nepal_tz)
    today = now.date()
    
    stats = {
        'timestamp': str(now),
        'total_companies': Company.objects.count(),
        'total_records': StockData.objects.count(),
        'today_records': StockData.objects.filter(scrape_date=today).count(),
        'market_status': 'unknown'
    }
    
    try:
        market_status = MarketStatus.objects.get(date=today)
        stats['market_status'] = 'open' if market_status.is_market_open else 'closed'
        stats['last_scraped'] = str(market_status.last_scraped) if market_status.last_scraped else 'never'
    except MarketStatus.DoesNotExist:
        stats['market_status'] = 'not_initialized'
    
    logger.info(f"❤️ Health check: {stats}")
    return stats

# Helper functions
def _is_market_open_now(now):
    """Check if market is open right now (Sun-Thu, 11AM-3PM)"""
    # Sunday=6, Monday=0, Tuesday=1, Wednesday=2, Thursday=3
    if now.weekday() not in [6, 0, 1, 2, 3]:
        return False
    
    current_time = now.time()
    market_open = time_obj(11, 0)  # 11:00 AM
    market_close = time_obj(15, 0)  # 3:00 PM
    
    return market_open <= current_time <= market_close

def _is_closing_time(now):
    """Check if it's closing time (2:45 PM - 3:15 PM)"""
    current_time = now.time()
    closing_start = time_obj(14, 45)  # 2:45 PM
    closing_end = time_obj(15, 15)    # 3:15 PM
    
    return closing_start <= current_time <= closing_end

def _mark_todays_data_as_closing(today):
    """Mark all today's latest data as closing data"""
    from .models import StockData
    from django.db.models import Max
    
    # Get latest scrape time for today
    latest_time = StockData.objects.filter(
        scrape_date=today
    ).aggregate(Max('scrape_time'))['scrape_time__max']
    
    if not latest_time:
        return 0
    
    # Mark those records as closing data
    updated = StockData.objects.filter(
        scrape_date=today,
        scrape_time=latest_time
    ).update(is_closing_data=True, data_source='closing')
    
    logger.info(f"Marked {updated} records as closing data for {today}")
    return updated