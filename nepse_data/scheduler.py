# nepse_data/scheduler.py
import logging
import threading
import time
from datetime import datetime
import pytz
from django.utils import timezone

logger = logging.getLogger(__name__)
NEPAL_TZ = pytz.timezone('Asia/Kathmandu')

def get_current_nepal_time():
    """Get current Nepal time"""
    return datetime.now(NEPAL_TZ)

def is_market_day_and_hours():
    """Check if it's a market day and within market hours"""
    current = get_current_nepal_time()
    weekday = current.weekday()  # 0=Monday, 6=Sunday
    hour = current.hour
    
    # Check if weekday (Monday-Friday)
    if weekday >= 5:
        return False, "Weekend - no trading"
    
    # Check market hours (11:00 AM to 3:00 PM)
    if hour < 11:
        return False, f"Market opens at 11:00 AM. Current: {current.strftime('%H:%M')}"
    
    if hour >= 15:
        return False, f"Market closed at 3:00 PM. Current: {current.strftime('%H:%M')}"
    
    return True, f"Market is open! Current: {current.strftime('%H:%M')}"

def check_and_scrape_if_needed():
    """
    Smart scraper that checks if we need to scrape today's data
    """
    from .scrapers import NepseScraper
    from .models import DailyStockData
    
    current = get_current_nepal_time()
    today = current.date()
    
    logger.info("=" * 60)
    logger.info(f"📅 DATE CHECK: {today}")
    logger.info(f"⏰ NEPAL TIME: {current.strftime('%H:%M:%S')}")
    logger.info(f"📆 DAY: {current.strftime('%A')}")
    logger.info("=" * 60)
    
    # Check if we already have today's data
    today_count = DailyStockData.objects.filter(date=today).count()
    
    if today_count > 0:
        logger.info(f"✅ Already have {today_count} records for today")
        
        # Check if market is still open - we might want to refresh
        market_open, msg = is_market_day_and_hours()
        if market_open:
            logger.info(f"🔄 Market is open. Consider refreshing data...")
            # You can add logic to refresh if market is still open
        return f"Already have {today_count} records for {today}"
    
    # Check if it's a market day
    market_open, msg = is_market_day_and_hours()
    
    if not market_open:
        logger.info(f"⏸️ {msg}")
        
        # If it's past market hours, check if website has today's data
        if current.hour >= 15 and current.hour < 24:
            logger.info("🌐 Trying to scrape today's closing data...")
            return scrape_today_data()
        else:
            return f"No action: {msg}"
    
    # Market is open - scrape data
    logger.info("🏦 Market is open! Scraping data...")
    return scrape_today_data()

def scrape_today_data():
    """Scrape today's data"""
    from .scrapers import NepseScraper
    from .models import DailyStockData
    
    current = get_current_nepal_time()
    today = current.date()
    
    logger.info(f"🚀 SCRAPING for {today}...")
    
    try:
        # Delete any existing data for today
        existing_count = DailyStockData.objects.filter(date=today).count()
        if existing_count > 0:
            logger.info(f"🗑️ Deleting {existing_count} old records...")
            DailyStockData.objects.filter(date=today).delete()
        
        # Scrape with retry
        data = NepseScraper.scrape_with_retry(max_retries=5)
        
        if data and len(data) > 50:
            saved = NepseScraper.save_to_database(data)
            logger.info(f"✅ Successfully saved {saved} records for {today}")
            
            # Update top performers
            try:
                NepseScraper.update_top_performers(today)
                logger.info("🏆 Updated top performers")
            except Exception as e:
                logger.error(f"⚠️ Failed to update top performers: {e}")
            
            # Log summary
            today_data = DailyStockData.objects.filter(date=today)
            gainers = today_data.filter(change_percent__gt=0).count()
            losers = today_data.filter(change_percent__lt=0).count()
            
            logger.info("=" * 50)
            logger.info(f"📊 TODAY'S SUMMARY ({today}):")
            logger.info(f"   Total Stocks: {saved}")
            logger.info(f"   Gainers: {gainers}")
            logger.info(f"   Losers: {losers}")
            logger.info(f"   Time: {current.strftime('%H:%M:%S')}")
            logger.info("=" * 50)
            
            return f"✅ Scraped {saved} records for {today}"
        else:
            logger.warning(f"⚠️ No data received for {today}")
            return f"⚠️ No data for {today}"
            
    except Exception as e:
        logger.error(f"❌ Error scraping {today}: {e}")
        return f"❌ Error: {e}"

def start_daily_scraper():
    """Start daily scraper that runs every 30 minutes"""
    import threading
    
    def scraper_loop():
        logger.info("🚀 Starting daily scraper service...")
        logger.info("🔄 Will check every 30 minutes for fresh data")
        
        while True:
            try:
                result = check_and_scrape_if_needed()
                logger.info(f"📋 Result: {result}")
                
                # Wait 30 minutes before next check
                logger.info("⏳ Waiting 30 minutes for next check...")
                time.sleep(30 * 60)  # 30 minutes
                
            except KeyboardInterrupt:
                logger.info("🛑 Scraper stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in scraper loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    # Start in background thread
    thread = threading.Thread(target=scraper_loop, daemon=True)
    thread.start()
    
    return True

def start():
    """Initialize the scraper"""
    current = get_current_nepal_time()
    
    logger.info("=" * 60)
    logger.info("🏦 NEPSE DAILY DATA SCRAPER")
    logger.info("=" * 60)
    logger.info(f"📅 Today: {current.strftime('%A, %B %d, %Y')}")
    logger.info(f"⏰ Nepal Time: {current.strftime('%H:%M:%S')}")
    logger.info("🕒 Market Hours: Mon-Fri, 11:00 AM - 3:00 PM")
    logger.info("🔄 Will check every 30 minutes for fresh data")
    logger.info("=" * 60)
    
    # Start immediate check
    threading.Thread(target=check_and_scrape_if_needed, daemon=True).start()
    
    # Start periodic scraper
    return start_daily_scraper()

start_scheduler = start