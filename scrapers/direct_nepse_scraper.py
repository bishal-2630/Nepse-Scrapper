#!/usr/bin/env python3
import requests
import json
import logging
from datetime import datetime
import time
from typing import Dict, List, Optional, Any
import warnings
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

logger = logging.getLogger(__name__)

class DirectNepseScraper:
    """Direct NEPSE API scraper using official endpoints"""
    
    def __init__(self):
        self.base_url = "https://www.nepalstock.com.np/api/nots"
        self.session = requests.Session()
        
        # CRITICAL: Disable SSL verification
        self.session.verify = False
        
        # Increase timeout and add retry logic
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nepalstock.com.np/',
            'Origin': 'https://www.nepalstock.com.np',
        })
        
        # Add retry adapter
        from requests.adapters import HTTPAdapter
        from requests.packages.urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
    
    def get_today_price_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get today's price data from NEPSE API"""
        print("🔍 Starting to fetch NEPSE data...")
        result = {'gainers': [], 'losers': []}
        
        try:
            # METHOD 1: Try to get today's price data for ALL stocks
            print("📊 Method 1: Fetching today's prices for all stocks...")
            all_stocks = self._get_todays_all_prices()
            
            if all_stocks:
                print(f"✅ Got {len(all_stocks)} total stocks")
                
                # Separate gainers and losers
                gainers_count = 0
                losers_count = 0
                
                for stock in all_stocks:
                    pct_change = stock.get('percentageChange', 0)
                    if pct_change > 0:
                        result['gainers'].append(stock)
                        gainers_count += 1
                    elif pct_change < 0:
                        result['losers'].append(stock)
                        losers_count += 1
                
                # Sort by percentage change
                result['gainers'].sort(key=lambda x: x.get('percentageChange', 0), reverse=True)
                result['losers'].sort(key=lambda x: x.get('percentageChange', 0))
                
                # Limit to top 10 each
                result['gainers'] = result['gainers'][:10]
                result['losers'] = result['losers'][:10]
                
                print(f"✅ Success: {len(result['gainers'])} gainers, {len(result['losers'])} losers")
                return result
            else:
                print("⚠️ Method 1 failed, trying Method 2...")
            
            # METHOD 2: Try direct gainers/losers endpoints
            print("📊 Method 2: Trying direct gainers/losers endpoints...")
            gainers = self._get_top_gainers_direct()
            losers = self._get_top_losers_direct()
            
            if gainers or losers:
                result['gainers'] = gainers[:10] if gainers else []
                result['losers'] = losers[:10] if losers else []
                print(f"✅ Direct method: {len(result['gainers'])} gainers, {len(result['losers'])} losers")
                return result
            
            print("❌ All methods failed to retrieve data")
            return result
            
        except Exception as e:
            print(f"❌ Error getting price data: {e}")
            import traceback
            traceback.print_exc()
            return result
    
    def _get_todays_all_prices(self) -> List[Dict[str, Any]]:
        """Get today's prices for all stocks"""
        try:
            # This is the main endpoint for today's prices
            url = f"{self.base_url}/security/today-price"
            
            print(f"🌐 Requesting: {url}")
            response = self.session.get(url, timeout=30)
            
            print(f"📡 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📄 Response type: {type(data)}")
                
                # Try to find stock data in response
                stocks = []
                
                # Common response structures
                if isinstance(data, dict):
                    print(f"📊 Dictionary keys: {list(data.keys())}")
                    
                    # Check for 'body' key
                    if 'body' in data and isinstance(data['body'], list):
                        print(f"📦 Found 'body' with {len(data['body'])} items")
                        stocks = self._process_stock_list(data['body'])
                    
                    # Check for 'data' key
                    elif 'data' in data and isinstance(data['data'], list):
                        print(f"📦 Found 'data' with {len(data['data'])} items")
                        stocks = self._process_stock_list(data['data'])
                    
                    # Check if any value is a list
                    else:
                        for key, value in data.items():
                            if isinstance(value, list):
                                print(f"📦 Found list in key '{key}' with {len(value)} items")
                                stocks = self._process_stock_list(value)
                                if stocks:
                                    break
                
                elif isinstance(data, list):
                    print(f"📦 Direct list with {len(data)} items")
                    stocks = self._process_stock_list(data)
                
                print(f"✅ Parsed {len(stocks)} valid stocks")
                return stocks
            
            else:
                print(f"⚠️ HTTP {response.status_code}")
                # Print first 200 chars of response for debugging
                print(f"Response preview: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print("⏰ Timeout while fetching today's prices")
        except requests.exceptions.ConnectionError:
            print("🔌 Connection error")
        except Exception as e:
            print(f"❌ Error in _get_todays_all_prices: {e}")
            import traceback
            traceback.print_exc()
        
        return []
    
    def _process_stock_list(self, raw_list: List) -> List[Dict[str, Any]]:
        """Process raw stock list"""
        stocks = []
        
        if not raw_list:
            return stocks
        
        print(f"🔧 Processing {len(raw_list)} raw items...")
        
        # Show first few items for debugging
        for i, item in enumerate(raw_list[:2]):
            if isinstance(item, dict):
                print(f"  Item {i+1}: {item.get('symbol', 'N/A')} - Keys: {list(item.keys())[:5]}")
            else:
                print(f"  Item {i+1} type: {type(item)}")
        
        for item in raw_list:
            stock = self._format_stock_data(item)
            if stock:
                stocks.append(stock)
        
        return stocks
    
    def _get_top_gainers_direct(self) -> List[Dict[str, Any]]:
        """Get top gainers directly"""
        try:
            endpoints = [
                f"{self.base_url}/top-ten/top-gainers",
                f"{self.base_url}/market/top-gainers",
            ]
            
            for url in endpoints:
                try:
                    print(f"🌐 Trying gainers endpoint: {url}")
                    response = self.session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        gainers = self._parse_top_ten_response(data)
                        if gainers:
                            print(f"✅ Got {len(gainers)} gainers from {url}")
                            return gainers
                            
                except Exception as e:
                    print(f"⚠️ Failed {url}: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ Error in _get_top_gainers_direct: {e}")
        
        return []
    
    def _get_top_losers_direct(self) -> List[Dict[str, Any]]:
        """Get top losers directly"""
        try:
            endpoints = [
                f"{self.base_url}/top-ten/top-losers",
                f"{self.base_url}/market/top-losers",
            ]
            
            for url in endpoints:
                try:
                    print(f"🌐 Trying losers endpoint: {url}")
                    response = self.session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        losers = self._parse_top_ten_response(data)
                        if losers:
                            print(f"✅ Got {len(losers)} losers from {url}")
                            return losers
                            
                except Exception as e:
                    print(f"⚠️ Failed {url}: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ Error in _get_top_losers_direct: {e}")
        
        return []
    
    def _parse_top_ten_response(self, data) -> List[Dict[str, Any]]:
        """Parse top-ten API response"""
        stocks = []
        
        try:
            raw_list = []
            
            if isinstance(data, dict):
                if 'body' in data and isinstance(data['body'], list):
                    raw_list = data['body']
                elif 'data' in data and isinstance(data['data'], list):
                    raw_list = data['data']
                else:
                    for key, value in data.items():
                        if isinstance(value, list):
                            raw_list = value
                            break
            
            elif isinstance(data, list):
                raw_list = data
            
            for item in raw_list:
                stock = self._format_stock_data(item)
                if stock:
                    stocks.append(stock)
        
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
        
        return stocks
    
    def _format_stock_data(self, item) -> Optional[Dict[str, Any]]:
        """Format stock data from API response"""
        try:
            if not isinstance(item, dict):
                return None
            
            # Get symbol
            symbol = None
            for field in ['symbol', 'companyCode', 'code', 'securityId']:
                if field in item and item[field]:
                    symbol = str(item[field]).strip().upper()
                    break
            
            if not symbol:
                return None
            
            # Get name
            name = symbol
            for field in ['companyName', 'securityName', 'name', 'company_name']:
                if field in item and item[field]:
                    name = str(item[field]).strip()
                    break
            
            # Get prices
            stock_data = {'symbol': symbol, 'securityName': name}
            
            # LTP/Close price
            for field in ['lastTradedPrice', 'ltp', 'closePrice', 'closingPrice', 'price', 'lastPrice']:
                if field in item and item[field] not in [None, '', '-']:
                    stock_data['ltp'] = self._parse_number(item[field])
                    break
            
            # Percentage change
            for field in ['percentageChange', 'percentChange', 'changePercent', 'changePercentage']:
                if field in item and item[field] not in [None, '', '-']:
                    stock_data['percentageChange'] = self._parse_number(item[field])
                    break
            
            # Previous close
            for field in ['previousClose', 'prevClose', 'yesterdayClose', 'previousClosingPrice']:
                if field in item and item[field] not in [None, '', '-']:
                    stock_data['previousClose'] = self._parse_number(item[field])
                    break
            
            # Point change
            for field in ['pointChange', 'difference', 'change', 'changeAmount']:
                if field in item and item[field] not in [None, '', '-']:
                    stock_data['pointChange'] = self._parse_number(item[field])
                    break
            
            # Ensure we have required fields
            if 'ltp' not in stock_data:
                return None
            
            # Calculate missing fields
            if 'percentageChange' not in stock_data and 'previousClose' in stock_data:
                if stock_data['previousClose'] and stock_data['previousClose'] > 0:
                    pct = ((stock_data['ltp'] - stock_data['previousClose']) / stock_data['previousClose']) * 100
                    stock_data['percentageChange'] = round(pct, 2)
            
            if 'pointChange' not in stock_data and 'previousClose' in stock_data:
                if stock_data['previousClose']:
                    stock_data['pointChange'] = round(stock_data['ltp'] - stock_data['previousClose'], 2)
            
            # Determine if gainer or loser
            pct = stock_data.get('percentageChange', 0)
            stock_data['is_gainer'] = pct > 0
            
            return {
                'symbol': stock_data['symbol'],
                'securityName': stock_data['securityName'],
                'ltp': stock_data.get('ltp'),
                'percentageChange': stock_data.get('percentageChange'),
                'previousClose': stock_data.get('previousClose'),
                'pointChange': stock_data.get('pointChange'),
                'is_gainer': stock_data.get('is_gainer', False)
            }
            
        except Exception as e:
            print(f"⚠️ Error formatting stock: {e}")
            return None
    
    def _parse_number(self, value) -> Optional[float]:
        """Parse number from various formats"""
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            if isinstance(value, str):
                value = value.strip()
                if value in ['', '-', 'N/A', 'NA', 'null', 'None']:
                    return None
                
                value = value.replace(',', '').replace(' ', '').replace('%', '').replace('Rs.', '')
                
                # Handle parentheses for negative numbers
                if value.startswith('(') and value.endswith(')'):
                    value = '-' + value[1:-1]
                
                return float(value)
            
            return float(value)
            
        except (ValueError, TypeError):
            return None

# Test function
def test_scraper():
    """Test the direct scraper"""
    print("="*70)
    print("🧪 Testing Direct NEPSE Scraper (SSL Disabled)")
    print("="*70)
    
    scraper = DirectNepseScraper()
    
    print("\n📥 Fetching data...")
    price_data = scraper.get_today_price_data()
    
    print(f"\n📊 Results:")
    print(f"   Gainers: {len(price_data['gainers'])}")
    print(f"   Losers: {len(price_data['losers'])}")
    
    if price_data['gainers']:
        print(f"\n🏆 Top Gainer:")
        g = price_data['gainers'][0]
        print(f"   Symbol: {g.get('symbol')}")
        print(f"   Name: {g.get('securityName')}")
        print(f"   LTP: {g.get('ltp')}")
        print(f"   Change: {g.get('percentageChange')}%")
        print(f"   Prev Close: {g.get('previousClose')}")
    
    if price_data['losers']:
        print(f"\n📉 Top Loser:")
        l = price_data['losers'][0]
        print(f"   Symbol: {l.get('symbol')}")
        print(f"   Name: {l.get('securityName')}")
        print(f"   LTP: {l.get('ltp')}")
        print(f"   Change: {l.get('percentageChange')}%")
        print(f"   Prev Close: {l.get('previousClose')}")
    
    print("\n" + "="*70)
    print("✅ Test Complete")
    print("="*70)
    
    return price_data

if __name__ == "__main__":
    test_scraper()
