#!/usr/bin/env python
# render_init.py - Run initial scraping on Render deployment

import os
import sys
import django
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nepse_scraper.settings')
django.setup()

from scrapers.tasks import scrape_24x7
from scrapers.models import StockData, Company
from django.utils import timezone

def main():
    print("="*50)
    print("🚀 Running initial setup for Render...")
    print("="*50)
    
    # Check current database state
    stock_count = StockData.objects.count()
    company_count = Company.objects.count()
    print(f"📊 Current database state:")
    print(f"   - StockData records: {stock_count}")
    print(f"   - Company records: {company_count}")
    
    # Run scraping if no data exists
    if stock_count == 0:
        print("\n🔍 No stock data found. Running initial scrape...")
        result = scrape_24x7()
        
        print(f"\n✅ Scraping result:")
        print(f"   - Success: {result.get('success', False)}")
        print(f"   - Records saved: {result.get('records_saved', 0)}")
        print(f"   - Message: {result.get('message', '')}")
        
        # Check again
        new_count = StockData.objects.count()
        print(f"\n📊 New stock count: {new_count}")
    else:
        print(f"\n✅ Data already exists ({stock_count} records). Skipping initial scrape.")
    
    # Show sample data
    latest_data = StockData.objects.order_by('-scrape_date', '-scrape_time')[:3]
    if latest_data.exists():
        print(f"\n📅 Latest data sample:")
        for stock in latest_data:
            print(f"   - {stock.symbol}: {stock.scrape_date} {stock.scrape_time}")
    
    print("\n" + "="*50)
    print("✅ Render setup completed!")
    print("="*50)

if __name__ == "__main__":
    main()