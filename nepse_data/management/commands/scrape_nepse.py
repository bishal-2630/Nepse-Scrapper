# scrape_nepse.py - Update the import and method calls
from django.core.management.base import BaseCommand
from nepse_data.scrapers import NepseScraper
from django.utils import timezone

class Command(BaseCommand):
    help = 'Scrape NEPSE data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            default='all',
            help='Task to run: all, today, historical, indices, companies'
        )
    
    def handle(self, *args, **options):
        task = options['task']
        
        self.stdout.write(f"Starting NEPSE scraping task: {task}")
        today = timezone.now().date()
        
        # Check if we already have today's data
        existing_count = DailyStockData.objects.filter(date=today).count()
        if existing_count > 50:  # If we already have data for today
            self.stdout.write(f"Already have {existing_count} records for today ({today})")
            if task != 'force':
                self.stdout.write("Use --task=force to scrape anyway")
                return
        
        if task in ['all', 'today', 'force']:
            self.scrape_today_data()
        
        if task in ['all', 'indices']:
            self.scrape_index_data()
        
        if task in ['all', 'companies']:
            self.scrape_company_list()
        
        # Update top performers
        if task in ['all', 'today', 'force']:
            self.update_top_performers()
        
        self.stdout.write(self.style.SUCCESS('Scraping completed!'))
    
    def scrape_today_data(self):
        self.stdout.write("Scraping today's stock prices...")
        data = NepseScraper.scrape_with_retry()
        if data:
            saved_count = NepseScraper.save_to_database(data)
            if saved_count > 0:
                self.stdout.write(self.style.SUCCESS(f"Today's data scraped successfully! Saved {saved_count} records"))
            else:
                self.stdout.write(self.style.ERROR("Failed to save today's data"))
        else:
            self.stdout.write(self.style.ERROR("No data received after retries"))

    def update_top_performers(self):
        self.stdout.write("Updating top gainers and losers...")
        try:
            NepseScraper.update_top_performers()
            self.stdout.write(self.style.SUCCESS("Top performers updated successfully"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to update top performers: {e}"))
    
    def scrape_index_data(self):
        self.stdout.write("Scraping index data...")
        # Implement index scraping
        self.stdout.write(self.style.WARNING("Index scraping not implemented yet"))
    
    def scrape_company_list(self):
        self.stdout.write("Scraping company list...")
        # Implement company list scraping
        self.stdout.write(self.style.WARNING("Company list scraping not implemented yet"))