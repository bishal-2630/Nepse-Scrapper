# scrapers/management/commands/scrape_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from scrapers.data_processor import NepseDataProcessor24x7
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrape NEPSE data using the 24/7 pipeline'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting NEPSE 24/7 data scraping..."))
        self.stdout.write("Note: Only available data will be saved (no estimated fields).")

        processor = NepseDataProcessor24x7()
        
        try:
            result = processor.execute_24x7_scraping()
            
            # Report results
            self.stdout.write(self.style.SUCCESS("\n✅ Scraping Completed Successfully!"))
            self.stdout.write("="*50)
            self.stdout.write(f"Results:")
            self.stdout.write(f"  • Data Source: {result.get('data_source_used', 'unknown')}")
            self.stdout.write(f"  • Records Saved: {result.get('records_saved', 0)}")
            self.stdout.write(f"  • Market Session: {result.get('market_session', 'unknown')}")
            self.stdout.write(f"  • Success: {result.get('success', False)}")
            self.stdout.write(f"  • Message: {result.get('message', '')}")
            
            # Database check
            from scrapers.models import StockData
            today = timezone.now().date()
            count = StockData.objects.filter(scrape_date=today).count()
            self.stdout.write(f"\n📊 Database: {count} total records for {today}")
            
            self.stdout.write(f"\nTimestamp: {result.get('timestamp', 'unknown')}")
            self.stdout.write("="*50)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Scraping Failed: {e}"))
            logger.error(f"Error in scrape_data command: {e}", exc_info=True)