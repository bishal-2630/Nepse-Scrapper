# nepse_data/tasks.py
from django_q.tasks import schedule
from django_q.models import Schedule
from django.utils import timezone

def schedule_daily_scraping():
    """Schedule daily scraping at 4:15 PM Nepal time (after market closes)"""
    # Remove existing schedules
    Schedule.objects.filter(func='nepse_data.tasks.scrape_daily_data').delete()
    
    # Schedule for Monday-Friday at 4:15 PM Nepal time
    schedule(
        'nepse_data.tasks.scrape_daily_data',
        name='Daily NEPSE Data Scraping',
        schedule_type=Schedule.CRON,
        cron='15 16 * * 1-5',  # 4:15 PM Mon-Fri
        repeats=-1,  # Repeat forever
    )
    print("Scheduled daily scraping at 4:15 PM (Mon-Fri)")

def scrape_daily_data():
    """Task to scrape daily data - Always fresh for today"""
    from .scrapers import NepseScraper
    from .models import DailyStockData
    from django.utils import timezone
    
    today = timezone.now().date()
    print(f"Starting automated scraping for {today}")
    
    # Delete any existing data for today first
    existing_count = DailyStockData.objects.filter(date=today).count()
    if existing_count > 0:
        print(f"Deleting {existing_count} existing records for {today}")
        DailyStockData.objects.filter(date=today).delete()
    
    try:
        # Scrape data
        data = NepseScraper.scrape_with_retry()
        if data:
            saved_count = NepseScraper.save_to_database(data)
            print(f"Saved {saved_count} fresh records")
            
            # Update top performers
            NepseScraper.update_top_performers(today)
            
            return f"Successfully scraped {saved_count} fresh records"
        else:
            return "No data received"
    except Exception as e:
        return f"Scraping failed: {str(e)}"