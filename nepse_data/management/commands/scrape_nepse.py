
from django.core.management.base import BaseCommand
from nepse_data.scrapers import NepseScraper
from nepse_data.models import DailyStockData
from django.utils import timezone

class Command(BaseCommand):
    help = 'Force scrape fresh data for today'
    
    def handle(self, *args, **options):
        today = timezone.now().date()
        
        self.stdout.write(f"📅 TODAY'S DATE: {today}")
        self.stdout.write(f"⏰ CURRENT TIME: {timezone.now().strftime('%H:%M:%S')}")
        
        # Delete existing data for today
        existing_count = DailyStockData.objects.filter(date=today).count()
        if existing_count > 0:
            self.stdout.write(f"🗑️ Deleting {existing_count} old records...")
            DailyStockData.objects.filter(date=today).delete()
        
        # Scrape fresh data
        self.stdout.write("🌐 Scraping FRESH data...")
        data = NepseScraper.scrape_with_retry(max_retries=3)
        
        if data and len(data) > 50:
            saved = NepseScraper.save_to_database(data)
            self.stdout.write(self.style.SUCCESS(f"✅ Saved {saved} FRESH records for {today}"))
            
            # Update top performers
            NepseScraper.update_top_performers(today)
            self.stdout.write(self.style.SUCCESS("🏆 Updated top performers"))
            
            # Show summary
            today_data = DailyStockData.objects.filter(date=today)
            gainers = today_data.filter(change_percent__gt=0).count()
            losers = today_data.filter(change_percent__lt=0).count()
            
            self.stdout.write("=" * 50)
            self.stdout.write(f"📊 TODAY'S SUMMARY:")
            self.stdout.write(f"   Total Stocks: {saved}")
            self.stdout.write(f"   Gainers: {gainers}")
            self.stdout.write(f"   Losers: {losers}")
            self.stdout.write("=" * 50)
        else:
            self.stdout.write(self.style.ERROR(f"❌ Failed to scrape data. Got {len(data) if data else 0} records"))