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
        
        if task in ['all', 'today']:
            self.scrape_today_data()
        
        if task in ['all', 'indices']:
            self.scrape_index_data()
        
        if task in ['all', 'companies']:
            self.scrape_company_list()
        
        self.stdout.write(self.style.SUCCESS('Scraping completed!'))
    
    def scrape_today_data(self):
        self.stdout.write("Scraping today's stock prices...")
        data = NepseScraper.scrape_today_prices()  # Fixed method name
        if data:
            saved_count = NepseScraper.save_to_database(data)  # Direct call
            if saved_count > 0:
                self.stdout.write(self.style.SUCCESS(f"Today's data scraped successfully! Saved {saved_count} records"))
            else:
                self.stdout.write(self.style.ERROR("Failed to save today's data"))
        else:
            self.stdout.write(self.style.ERROR("No data received"))
    
    def scrape_index_data(self):
        self.stdout.write("Scraping index data...")
        # Implement index scraping
        self.stdout.write(self.style.WARNING("Index scraping not implemented yet"))
    
    def scrape_company_list(self):
        self.stdout.write("Scraping company list...")
        # Implement company list scraping
        self.stdout.write(self.style.WARNING("Company list scraping not implemented yet"))