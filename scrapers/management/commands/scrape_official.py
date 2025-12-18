from django.core.management.base import BaseCommand
from django.utils import timezone
from scrapers.scraper import NEPSEAPIScraper
from scrapers.models import Company, StockData, MarketStatus
import logging
import requests

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrape data from official NEPSE API'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test connection only'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force scraping even if connection test fails'
        )
    
    def test_connection(self, scraper):
        """Test connection to NEPSE API"""
        try:
            # Try to use the test_connection method if it exists
            if hasattr(scraper, 'test_connection'):
                return scraper.test_connection()
            
            # Otherwise, test manually
            url = "https://www.nepalstock.com.np/api/nots/market-summary"
            response = requests.get(url, params={'page': 0, 'size': 1}, 
                                  timeout=10, verify=False)
            return response.status_code == 200
            
        except:
            return False
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting NEPSE data scraping from official API..."))
        
        scraper = NEPSEAPIScraper()
        
        if options['test']:
            # Test connection only
            if self.test_connection(scraper):
                self.stdout.write("✓ Connection to NEPSE API successful")
            else:
                self.stdout.write(self.style.ERROR("✗ Connection to NEPSE API failed"))
            return
        
        # Test connection first (unless forced)
        if not options['force']:
            if not self.test_connection(scraper):
                self.stdout.write(self.style.ERROR("Cannot connect to NEPSE API. Use --force to attempt anyway."))
                return
        
        self.stdout.write("✓ Connected to NEPSE API (or forced)")
        
        # Get market data
        self.stdout.write("Fetching market data...")
        raw_data = scraper.get_market_data(page=0, size=500)
        
        if not raw_data:
            self.stdout.write(self.style.ERROR("Failed to fetch market data"))
            return
        
        self.stdout.write(f"✓ Received market data")
        
        # Parse data
        parsed_data = scraper.parse_market_data(raw_data)
        
        if not parsed_data:
            self.stdout.write(self.style.ERROR("Failed to parse market data"))
            return
        
        self.stdout.write(f"✓ Parsed {len(parsed_data)} stocks")
        
        # Get current time
        current_time = timezone.now()
        scrape_date = current_time.date()
        scrape_time = current_time.time()
        
        # Save to database
        saved_companies = 0
        saved_stocks = 0
        
        for stock_data in parsed_data:
            try:
                symbol = stock_data.get('symbol', '').strip()
                security_name = stock_data.get('security_name', '').strip()
                
                if not symbol:
                    continue
                
                # Get or create company
                company, created = Company.objects.get_or_create(
                    symbol=symbol,
                    defaults={
                        'name': security_name,
                        'is_active': True
                    }
                )
                
                if created:
                    saved_companies += 1
                
                # Update company name if it changed
                if not created and company.name != security_name:
                    company.name = security_name
                    company.save()
                
                # Check if stock data already exists for this timestamp
                existing = StockData.objects.filter(
                    company=company,
                    scrape_date=scrape_date,
                    scrape_time=scrape_time
                ).exists()
                
                if existing:
                    continue  # Skip if already exists
                
                # Create stock data record
                StockData.objects.create(
                    company=company,
                    open_price=stock_data.get('open_price'),
                    high_price=stock_data.get('high_price'),
                    low_price=stock_data.get('low_price'),
                    close_price=stock_data.get('close_price'),
                    last_traded_price=stock_data.get('last_traded_price'),
                    volume=stock_data.get('volume', 0),
                    previous_close=stock_data.get('previous_close'),
                    difference=stock_data.get('difference'),
                    percentage_change=stock_data.get('percentage_change'),
                    turnover=stock_data.get('turnover'),
                    transaction_count=stock_data.get('transaction_count', 0),
                    scrape_date=scrape_date,
                    scrape_time=scrape_time
                )
                
                saved_stocks += 1
                
            except Exception as e:
                self.stdout.write(f"⚠ Error saving {stock_data.get('symbol')}: {e}")
                continue
        
        # Get top gainers and losers
        self.stdout.write("\nFetching top gainers and losers...")
        top_data = scraper.get_top_gainers_losers()
        
        if top_data:
            gainers_count = len(top_data.get('top_gainers', []))
            losers_count = len(top_data.get('top_losers', []))
            self.stdout.write(f"✓ Found {gainers_count} gainers and {losers_count} losers")
        
        # Update market status
        self.stdout.write("\nUpdating market status...")
        
        # Calculate market statistics
        market_stats = scraper.calculate_market_stats(parsed_data)
        
        market_status, created = MarketStatus.objects.update_or_create(
            date=scrape_date,
            defaults={
                'is_market_open': True,  # If we got data, market is open
                'last_scraped': current_time,
                'total_turnover': market_stats.get('total_turnover', 0),
                'total_volume': market_stats.get('total_volume', 0),
                'total_transactions': market_stats.get('total_transactions', 0),
            }
        )
        
        self.stdout.write(f"✓ Market status updated")
        
        # Show results
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("SCRAPING RESULTS:"))
        self.stdout.write("="*50)
        self.stdout.write(f"Companies processed: {saved_companies} new, {len(parsed_data)} total")
        self.stdout.write(f"Stock records saved: {saved_stocks}")
        self.stdout.write(f"Market turnover: {market_stats.get('total_turnover', 0):,.2f}")
        self.stdout.write(f"Market volume: {market_stats.get('total_volume', 0):,}")
        self.stdout.write("="*50)
        
        # Show final database stats
        self.stdout.write("\n" + "="*50)
        self.stdout.write("DATABASE STATISTICS:")
        self.stdout.write("="*50)
        self.stdout.write(f"Total Companies: {Company.objects.count()}")
        self.stdout.write(f"Total Stock Data: {StockData.objects.count()}")
        self.stdout.write(f"Total Market Status: {MarketStatus.objects.count()}")
        self.stdout.write("="*50)
        
        self.stdout.write(self.style.SUCCESS("\nScraping completed successfully!"))
        self.stdout.write(f"Data scraped at: {current_time}")