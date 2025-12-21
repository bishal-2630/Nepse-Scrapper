#!/usr/bin/env python
# Test script for NEPSE scraping
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nepse_scraper.settings')
django.setup()

from scrapers.data_processor import NepseDataProcessor24x7
from scrapers.models import StockData, Company
from django.utils import timezone

def test_scraping():
    """Test the scraping functionality"""
    print("="*50)
    print("Testing NEPSE Scraping System")
    print("="*50)
    
    # Check current database state
    print("\n1. Current Database State:")
    print(f"   Companies: {Company.objects.count()}")
    print(f"   Stock Records: {StockData.objects.count()}")
    
    if StockData.objects.exists():
        latest = StockData.objects.order_by('-scrape_date', '-scrape_time').first()
        print(f"   Latest record: {latest.symbol} on {latest.scrape_date} {latest.scrape_time}")
    
    # Test scraping
    print("\n2. Testing Scraping...")
    try:
        processor = NepseDataProcessor24x7()
        
        print("   Updating companies...")
        created, updated = processor.update_companies()
        print(f"   Companies: {created} created, {updated} updated")
        
        print("   Starting scraping...")
        result = processor.execute_24x7_scraping()
        
        print("\n3. Scraping Results:")
        print(f"   Success: {result.get('success')}")
        print(f"   Records Saved: {result.get('records_saved')}")
        print(f"   Data Source: {result.get('data_source_used')}")
        print(f"   Message: {result.get('message')}")
        
        # Check updated database
        print("\n4. Updated Database State:")
        print(f"   Companies: {Company.objects.count()}")
        print(f"   Stock Records: {StockData.objects.count()}")
        
        if result.get('records_saved', 0) > 0:
            latest = StockData.objects.order_by('-scrape_date', '-scrape_time').first()
            print(f"   New record: {latest.symbol} - LTP: {latest.last_traded_price}, Change: {latest.percentage_change}%")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\n" + "="*50)
    print("Testing API Endpoints")
    print("="*50)
    
    # You would need requests module for this
    # For now, just check database
    from scrapers.models import StockData
    
    latest_date = StockData.objects.aggregate(latest_date=Max('scrape_date'))['latest_date']
    if latest_date:
        latest_stocks = StockData.objects.filter(scrape_date=latest_date).count()
        print(f"Latest date: {latest_date}")
        print(f"Records for latest date: {latest_stocks}")
        
        # Show some sample data
        samples = StockData.objects.filter(scrape_date=latest_date)[:5]
        print("\nSample data:")
        for stock in samples:
            print(f"  {stock.symbol}: {stock.last_traded_price} ({stock.percentage_change}%)")
    else:
        print("No data available for API testing")

if __name__ == "__main__":
    success = test_scraping()
    
    if success:
        test_api_endpoints()
        print("\n" + "="*50)
        print("✅ TEST PASSED - System is working!")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("❌ TEST FAILED - Check the errors above")
        print("="*50)
        sys.exit(1) 