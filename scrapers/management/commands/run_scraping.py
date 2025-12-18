from django.core.management.base import BaseCommand
from django.utils import timezone
import sys

class Command(BaseCommand):
    help = 'Run NEPSE data scraping manually'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--method',
            type=str,
            default='primary',
            choices=['primary', 'backup', 'test'],
            help='Scraping method to use'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force scraping even outside market hours'
        )
    
    def handle(self, *args, **options):
        method = options['method']
        force = options['force']
        
        self.stdout.write(self.style.SUCCESS(f"Starting NEPSE scraping with method: {method}"))
        
        try:
            # Import tasks inside the function to avoid circular imports
            from scrapers.tasks import (
                scrape_nepse_data_api, 
                scrape_nepse_backup_data,
                test_scraping,
                daily_scraping_job
            )
            
            # Check if we should force scraping
            if not force:
                # Check market hours
                current_hour = timezone.now().hour
                market_start = 11
                market_end = 15
                
                if not (market_start <= current_hour < market_end):
                    self.stdout.write(self.style.WARNING(
                        f"Outside market hours ({market_start}:00-{market_end}:00). "
                        "Use --force to override."
                    ))
                    return
            
            if method == 'primary':
                self.stdout.write("Running primary scraping (NepseAPI-Unofficial)...")
                result = scrape_nepse_data_api.delay()
                self.stdout.write(f"✓ Task started with ID: {result.id}")
                
            elif method == 'backup':
                self.stdout.write("Running backup scraping (Original NEPSE API)...")
                result = scrape_nepse_backup_data.delay()
                self.stdout.write(f"✓ Task started with ID: {result.id}")
                
            elif method == 'test':
                self.stdout.write("Running test scraping...")
                result = test_scraping.delay()
                self.stdout.write(f"✓ Test task started with ID: {result.id}")
            
            self.stdout.write(self.style.SUCCESS("\nScraping task started successfully!"))
            self.stdout.write("\nNext steps:")
            self.stdout.write("1. Check Celery worker logs for progress")
            self.stdout.write("2. Check the database for new records")
            self.stdout.write("3. Visit http://localhost:8000/api/ to view data")
            
            # Show current database stats
            self.show_database_stats()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error starting scraping: {e}"))
            import traceback
            traceback.print_exc()
    
    def show_database_stats(self):
        """Show current database statistics"""
        try:
            from scrapers.models import Company, StockData, MarketStatus
            
            self.stdout.write("\n" + "="*50)
            self.stdout.write("CURRENT DATABASE STATISTICS:")
            self.stdout.write("="*50)
            
            # Company stats
            try:
                company_count = Company.objects.count()
                active_companies = Company.objects.filter(is_active=True).count()
                self.stdout.write(f"Companies: {company_count} total, {active_companies} active")
            except:
                self.stdout.write("Companies: Table not created yet")
            
            # StockData stats
            try:
                stock_count = StockData.objects.count()
                if stock_count > 0:
                    latest_date = StockData.objects.latest('scrape_date').scrape_date
                    today_count = StockData.objects.filter(scrape_date=timezone.now().date()).count()
                    self.stdout.write(f"Stock Records: {stock_count} total")
                    self.stdout.write(f"  Latest date: {latest_date}")
                    self.stdout.write(f"  Today's records: {today_count}")
                else:
                    self.stdout.write("Stock Records: 0 (no data yet)")
            except:
                self.stdout.write("Stock Records: Table not created yet")
            
            # MarketStatus stats
            try:
                market_status_count = MarketStatus.objects.count()
                if market_status_count > 0:
                    latest_status = MarketStatus.objects.latest('date')
                    self.stdout.write(f"Market Status Records: {market_status_count}")
                    self.stdout.write(f"  Latest: {latest_status.date} - {'Open' if latest_status.is_market_open else 'Closed'}")
                else:
                    self.stdout.write("Market Status Records: 0 (no data yet)")
            except:
                self.stdout.write("Market Status Records: Table not created yet")
            
            self.stdout.write("="*50)
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not fetch database stats: {e}"))