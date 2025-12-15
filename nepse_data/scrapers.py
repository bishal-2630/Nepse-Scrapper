import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import json
import time
from django.utils import timezone
from .models import Company, DailyStockData

class NepseScraper:
    """Main scraper for NEPSE data"""
    
    @staticmethod
    def scrape_today_prices():
        """
        Scrape today's stock prices from Merolagani (a popular Nepali financial site)
        Returns: List of stock data dictionaries
        """
        try:
            url = "https://merolagani.com/LatestMarket.aspx"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            print("Scraping data from Merolagani...")
            response = requests.get(url, headers=headers, timeout=30)
            
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
                            stock = {
                                'symbol': cols[0].text.strip(),
                                'ltp': cols[1].text.strip().replace(',', ''),  # Last Traded Price
                                'change': cols[2].text.strip(),
                                'percent_change': cols[3].text.strip().replace('%', ''),
                                'open': cols[4].text.strip().replace(',', ''),
                                'high': cols[5].text.strip().replace(',', ''),
                                'low': cols[6].text.strip().replace(',', ''),
                                'volume': cols[7].text.strip().replace(',', '') if len(cols) > 7 else '0',
                                'date': timezone.now().date()
                            }
                            stocks_data.append(stock)
                    
                    print(f"Successfully scraped {len(stocks_data)} stocks")
                    return stocks_data
                else:
                    print("Table not found on the page")
                    return []
            else:
                print(f"Failed to fetch page. Status: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error scraping data: {e}")
            return []

    @staticmethod
    def scrape_share_sansar():
        """
        Alternative scraping from ShareSansar
        """
        try:
            url = "https://www.sharesansar.com/live-trading"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers)
          
            return []
            
        except Exception as e:
            print(f"Error scraping ShareSansar: {e}")
            return []

    @staticmethod
    def save_to_database(stock_data):
        """Save scraped data to database"""
        saved_count = 0
        today = timezone.now().date()
        
        for data in stock_data:
            try:
          
                company, created = Company.objects.get_or_create(
                    symbol=data['symbol'],
                    defaults={'name': data['symbol']}  
                )
                
               
                daily_data, created = DailyStockData.objects.update_or_create(
                    company=company,
                    date=today,
                    defaults={
                        'open_price': float(data['open']) if data['open'] else 0,
                        'high_price': float(data['high']) if data['high'] else 0,
                        'low_price': float(data['low']) if data['low'] else 0,
                        'close_price': float(data['ltp']) if data['ltp'] else 0,
                        'volume': int(data['volume']) if data['volume'] else 0,
                        'change': float(data['change']) if data['change'] else 0,
                        'change_percent': float(data['percent_change']) if data['percent_change'] else 0,
                    }
                )
                
                saved_count += 1
                
            except Exception as e:
                print(f"Error saving {data.get('symbol', 'unknown')}: {e}")
        
        return saved_count
    
class DataProcessor:
    """Process and save scraped data"""
    
    @staticmethod
    def process_today_price_data(data):
        """Process today's price data"""
        return NepseScraper.save_to_database(data)
    
    @staticmethod
    def process_index_data(data):
        """Process index data"""
       
        return True
    
@staticmethod
def calculate_top_gainers_losers(date=None):
    """
    Calculate top gainers and losers for a given date
    """
    if not date:
        date = timezone.now().date()
    
    
    daily_data = DailyStockData.objects.filter(date=date)
    
 
    gainers = daily_data.filter(change_percent__gt=0).order_by('-change_percent')[:10]
    
   
    losers = daily_data.filter(change_percent__lt=0).order_by('change_percent')[:10]
    

    top_gainers = []
    for i, data in enumerate(gainers, 1):
        top_gainers.append({
            'rank': i,
            'symbol': data.company.symbol,
            'company_name': data.company.name,
            'change_percent': float(data.change_percent),
            'change': float(data.change),
            'close_price': float(data.close_price),
            'volume': data.volume,
            'sector': data.company.sector or 'N/A'
        })
    
    top_losers = []
    for i, data in enumerate(losers, 1):
        top_losers.append({
            'rank': i,
            'symbol': data.company.symbol,
            'company_name': data.company.name,
            'change_percent': float(data.change_percent),
            'change': float(data.change),
            'close_price': float(data.close_price),
            'volume': data.volume,
            'sector': data.company.sector or 'N/A'
        })
    
    return {
        'date': date,
        'top_gainers': top_gainers,
        'top_losers': top_losers,
        'total_gainers': len(top_gainers),
        'total_losers': len(top_losers)
    }



@staticmethod
def scrape_with_retry(max_retries=3):
    """Scrape with retry logic"""
    for attempt in range(max_retries):
        try:
            data = NepseScraper.scrape_today_prices()
            if data and len(data) > 10: 
                return data
            print(f"Attempt {attempt + 1}: Got insufficient data ({len(data) if data else 0} records)")
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(5)  # Wait before retry
    
    return []

@staticmethod
def update_top_performers(date=None):
    """Update TopGainers and TopLosers tables"""
    from .models import TopGainers, TopLosers
    
    if not date:
        date = timezone.now().date()
    
    # Get today's data
    daily_data = DailyStockData.objects.filter(date=date)
    
    # Clear old entries for this date
    TopGainers.objects.filter(date=date).delete()
    TopLosers.objects.filter(date=date).delete()
    
    # Get top 10 gainers
    gainers = daily_data.filter(change_percent__gt=0).order_by('-change_percent')[:10]
    for i, data in enumerate(gainers, 1):
        TopGainers.objects.create(
            date=date,
            rank=i,
            company=data.company,
            change_percent=data.change_percent,
            volume=data.volume,
            close_price=data.close_price
        )
    
    # Get top 10 losers
    losers = daily_data.filter(change_percent__lt=0).order_by('change_percent')[:10]
    for i, data in enumerate(losers, 1):
        TopLosers.objects.create(
            date=date,
            rank=i,
            company=data.company,
            change_percent=data.change_percent,
            volume=data.volume,
            close_price=data.close_price
        )
    
    print(f"Updated top performers for {date}")