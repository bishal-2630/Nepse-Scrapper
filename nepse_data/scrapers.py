# nepse_data/scrapers.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, date
import json
import time
import random
from django.utils import timezone
from .models import Company, DailyStockData

class NepseScraper:
    """Main scraper for NEPSE data"""
    
    @staticmethod
    def get_headers():
        """Get rotating headers to avoid blocking"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
    
    @staticmethod
    def scrape_today_prices():
        """
        Scrape today's stock prices from Merolagani with better error handling
        """
        try:
            url = "https://merolagani.com/LatestMarket.aspx"
            headers = NepseScraper.get_headers()
            
            print(f"🕒 Scraping data at {timezone.now().strftime('%H:%M:%S')}...")
            
            # Use shorter timeout with retry logic
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find the table with stock data
                table = soup.find('table', {'class': 'table table-hover live-trading sortable'})
                
                if table:
                    stocks_data = []
                    rows = table.find_all('tr')[1:]  # Skip header row
                    
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 7:
                            # Get TODAY'S date
                            today_date = timezone.now().date()
                            
                            # Parse numeric values safely
                            try:
                                ltp = float(cols[1].text.strip().replace(',', '')) if cols[1].text.strip().replace(',', '') else 0
                            except:
                                ltp = 0
                                
                            try:
                                change_val = float(cols[2].text.strip()) if cols[2].text.strip() else 0
                            except:
                                change_val = 0
                                
                            try:
                                change_percent = float(cols[3].text.strip().replace('%', '')) if cols[3].text.strip().replace('%', '') else 0
                            except:
                                change_percent = 0
                                
                            try:
                                open_price = float(cols[4].text.strip().replace(',', '')) if cols[4].text.strip().replace(',', '') else 0
                            except:
                                open_price = 0
                                
                            try:
                                high_price = float(cols[5].text.strip().replace(',', '')) if cols[5].text.strip().replace(',', '') else 0
                            except:
                                high_price = 0
                                
                            try:
                                low_price = float(cols[6].text.strip().replace(',', '')) if cols[6].text.strip().replace(',', '') else 0
                            except:
                                low_price = 0
                                
                            try:
                                volume = int(cols[7].text.strip().replace(',', '')) if len(cols) > 7 and cols[7].text.strip().replace(',', '') else 0
                            except:
                                volume = 0
                            
                            stock = {
                                'symbol': cols[0].text.strip(),
                                'ltp': ltp,
                                'change': change_val,
                                'percent_change': change_percent,
                                'open': open_price,
                                'high': high_price,
                                'low': low_price,
                                'volume': volume,
                                'date': today_date
                            }
                            stocks_data.append(stock)
                    
                    print(f"✅ Successfully scraped {len(stocks_data)} stocks")
                    return stocks_data
                else:
                    print("⚠️ Table not found - trying alternative method...")
                    return NepseScraper.scrape_alternative()
            else:
                print(f"⚠️ Status {response.status_code} - trying alternative...")
                return NepseScraper.scrape_alternative()
                
        except requests.exceptions.Timeout:
            print("⏰ Request timeout - trying alternative...")
            return NepseScraper.scrape_alternative()
        except requests.exceptions.ConnectionError:
            print("🔌 Connection error - trying alternative...")
            return NepseScraper.scrape_alternative()
        except Exception as e:
            print(f"❌ Error: {e} - trying alternative...")
            return NepseScraper.scrape_alternative()
    
    @staticmethod
    def scrape_alternative():
        """Try alternative data source"""
        try:
            print("🔄 Trying alternative source (ShareSansar)...")
            url = "https://www.sharesansar.com/"
            headers = NepseScraper.get_headers()
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to find stock data (this is example - adjust based on actual site structure)
                # You'll need to inspect sharesansar.com to find the correct selectors
                stocks_data = []
                print("⚠️ ShareSansar structure needs to be implemented")
                return stocks_data
            else:
                print(f"⚠️ Alternative source failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Alternative source error: {e}")
            return []
    
    @staticmethod
    def scrape_demo_data():
        """Generate demo data for testing when real scraping fails"""
        print("🧪 Generating demo data for testing...")
        
        today_date = timezone.now().date()
        demo_symbols = [
            'NLIC', 'NIB', 'NBL', 'SCB', 'HBL', 'NBB', 'EBL', 'MBL',
            'SBI', 'NTC', 'NIFRA', 'SHIVM', 'NHDL', 'CHCL', 'NCCB'
        ]
        
        stocks_data = []
        for symbol in demo_symbols:
            stocks_data.append({
                'symbol': symbol,
                'ltp': round(random.uniform(500, 2000), 2),
                'change': round(random.uniform(-50, 50), 2),
                'percent_change': round(random.uniform(-5, 5), 2),
                'open': round(random.uniform(500, 2000), 2),
                'high': round(random.uniform(500, 2000), 2),
                'low': round(random.uniform(500, 2000), 2),
                'volume': random.randint(1000, 100000),
                'date': today_date
            })
        
        print(f"🧪 Generated {len(stocks_data)} demo records")
        return stocks_data
    
    @staticmethod
    def save_to_database(stock_data):
        """Save scraped data to database"""
        saved_count = 0
        today = timezone.now().date()
        
        if not stock_data:
            print("⚠️ No data to save")
            return 0
        
        print(f"💾 Saving {len(stock_data)} records for {today}...")
        
        for data in stock_data:
            try:
                # Force today's date
                data['date'] = today
                
                company, created = Company.objects.get_or_create(
                    symbol=data['symbol'],
                    defaults={
                        'name': data['symbol'],
                        'sector': 'Unknown'
                    }
                )
                
                daily_data, created = DailyStockData.objects.update_or_create(
                    company=company,
                    date=today,
                    defaults={
                        'open_price': data['open'],
                        'high_price': data['high'],
                        'low_price': data['low'],
                        'close_price': data['ltp'],
                        'volume': data['volume'],
                        'change': data['change'],
                        'change_percent': data['percent_change'],
                    }
                )
                
                saved_count += 1
                
            except Exception as e:
                print(f"⚠️ Error saving {data.get('symbol', 'unknown')}: {e}")
        
        print(f"✅ Saved {saved_count} records")
        return saved_count
    
    @staticmethod
    def scrape_with_retry(max_retries=3, use_demo_on_fail=True):
        """Scrape with retry logic"""
        today = timezone.now().date()
        print(f"🔄 Starting retry scraping for {today}...")
        
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries}")
                
                if attempt > 0:
                    wait_time = 2  # Shorter wait time
                    print(f"Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                
                data = NepseScraper.scrape_today_prices()
                
                if data and len(data) > 10:
                    print(f"✅ Got {len(data)} records")
                    return data
                else:
                    print(f"⚠️ Insufficient data ({len(data) if data else 0} records)")
                    
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
        
        print(f"❌ Failed after {max_retries} attempts")
        
        # Use demo data if all attempts fail
        if use_demo_on_fail:
            print("🔄 Falling back to demo data...")
            return NepseScraper.scrape_demo_data()
        
        return []