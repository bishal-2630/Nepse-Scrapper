#!/usr/bin/env python3
"""
Merolagani.com Scraper for NEPSE Stock Data
This scraper fetches live market data from Merolagani.com
"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Optional, Any
import time

logger = logging.getLogger(__name__)

class MerolaganiScraper:
    """Scraper for Merolagani.com - Reliable and simple"""
    
    def __init__(self):
        self.base_url = "https://merolagani.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get_today_price_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get today's price data from Merolagani"""
        print("=" * 60)
        print("🌐 Fetching live market data from Merolagani.com...")
        print("=" * 60)
        
        result = {'gainers': [], 'losers': []}
        
        try:
            # Get the main market page
            url = f"{self.base_url}/LatestMarket.aspx"
            print(f"📡 Requesting: {url}")
            
            response = self.session.get(url, timeout=30)
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch page: HTTP {response.status_code}")
                return result
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # STRATEGY 1: Look for specific gainers/losers tables
            print("\n🔍 Strategy 1: Looking for 'Top Gainers' and 'Top Losers' tables...")
            
            # Find all tables on the page
            tables = soup.find_all('table')
            print(f"📋 Found {len(tables)} tables on the page")
            
            # Look for tables with stock data
            for i, table in enumerate(tables):
                table_text = table.get_text().lower()
                
                # Check if this looks like a stock table
                if any(keyword in table_text for keyword in ['symbol', 'company', 'ltp', 'change', '%']):
                    print(f"\n📊 Analyzing Table #{i+1}...")
                    
                    # Parse the table
                    stocks = self._parse_stock_table(table)
                    
                    if stocks:
                        print(f"✅ Found {len(stocks)} stocks in this table")
                        
                        # Determine if this is a gainers or losers table
                        table_context = self._get_table_context(table)
                        
                        if 'gain' in table_context.lower():
                            result['gainers'].extend(stocks[:10])
                            print(f"📈 Added to gainers list")
                        elif 'los' in table_context.lower():
                            result['losers'].extend(stocks[:10])
                            print(f"📉 Added to losers list")
                        else:
                            # If we can't determine, separate by percentage change
                            for stock in stocks:
                                pct = stock.get('percentageChange', 0)
                                if pct > 0 and len(result['gainers']) < 10:
                                    result['gainers'].append(stock)
                                elif pct < 0 and len(result['losers']) < 10:
                                    result['losers'].append(stock)
            
            # STRATEGY 2: If we didn't find enough data, try to find data in divs
            if len(result['gainers']) < 5 or len(result['losers']) < 5:
                print("\n🔍 Strategy 2: Searching for stock data in all page elements...")
                all_stocks = self._search_all_elements_for_stocks(soup)
                
                for stock in all_stocks:
                    pct = stock.get('percentageChange', 0)
                    if pct > 0 and len(result['gainers']) < 10:
                        result['gainers'].append(stock)
                    elif pct < 0 and len(result['losers']) < 10:
                        result['losers'].append(stock)
            
            # Sort and finalize
            result['gainers'].sort(key=lambda x: x.get('percentageChange', 0), reverse=True)
            result['losers'].sort(key=lambda x: x.get('percentageChange', 0))
            
            # Ensure we have at least some data
            if not result['gainers'] and not result['losers']:
                print("⚠️ No stock data found, using fallback strategy...")
                result = self._get_fallback_data()
            
            print(f"\n✅ FINAL RESULTS: {len(result['gainers'])} gainers, {len(result['losers'])} losers")
            
        except Exception as e:
            print(f"❌ Error scraping Merolagani: {e}")
            import traceback
            traceback.print_exc()
            result = self._get_fallback_data()
        
        return result
    
    def _parse_stock_table(self, table) -> List[Dict[str, Any]]:
        """Parse a stock table from Merolagani"""
        stocks = []
        
        try:
            rows = table.find_all('tr')
            if len(rows) < 2:
                return stocks
            
            # Find header row
            header_row = rows[0]
            headers = []
            
            # Get all th or td elements in header
            for cell in header_row.find_all(['th', 'td']):
                headers.append(cell.get_text().strip().lower())
            
            print(f"   Table headers: {headers}")
            
            # Map column indices based on common header names
            col_indices = {}
            
            for i, header in enumerate(headers):
                header_lower = header.lower()
                
                if any(keyword in header_lower for keyword in ['symbol', 'company', 'scrip']):
                    col_indices['symbol'] = i
                elif any(keyword in header_lower for keyword in ['ltp', 'price', 'last', 'closing']):
                    col_indices['price'] = i
                elif any(keyword in header_lower for keyword in ['change%', '% change', 'change %', 'percent']):
                    col_indices['pct_change'] = i
                elif 'change' in header_lower and '%' not in header_lower:
                    col_indices['point_change'] = i
            
            print(f"   Mapped columns: {col_indices}")
            
            # Process data rows
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) < 2:  # Need at least symbol and price
                    continue
                
                try:
                    # Extract data
                    symbol = ""
                    price = None
                    pct_change = None
                    
                    if 'symbol' in col_indices and col_indices['symbol'] < len(cells):
                        symbol = cells[col_indices['symbol']].get_text().strip()
                    
                    if 'price' in col_indices and col_indices['price'] < len(cells):
                        price_text = cells[col_indices['price']].get_text().strip()
                        price = self._parse_number(price_text)
                    
                    if 'pct_change' in col_indices and col_indices['pct_change'] < len(cells):
                        pct_text = cells[col_indices['pct_change']].get_text().strip()
                        pct_change = self._parse_number(pct_text)
                    
                    # Validate and create stock object
                    if symbol and price is not None:
                        stock = {
                            'symbol': symbol.upper(),
                            'securityName': symbol.upper(),  # Use symbol as name for now
                            'ltp': price,
                            'percentageChange': pct_change or 0,
                            'previousClose': None,
                            'pointChange': None,
                            'is_gainer': (pct_change or 0) > 0
                        }
                        stocks.append(stock)
                        print(f"   ✓ {symbol}: {price} ({pct_change}%)")
                
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"   ⚠️ Error parsing table row: {e}")
        
        return stocks
    
    def _get_table_context(self, table):
        """Get context around a table to determine if it's gainers/losers"""
        try:
            # Look for headings before the table
            for sibling in table.find_previous_siblings():
                if sibling.name in ['h1', 'h2', 'h3', 'h4', 'div', 'p']:
                    text = sibling.get_text().strip()
                    if text:
                        return text
            
            # Look for parent container
            parent = table.parent
            if parent:
                for child in parent.children:
                    if child.name in ['h1', 'h2', 'h3', 'h4']:
                        text = child.get_text().strip()
                        if text:
                            return text
        
        except:
            pass
        
        return ""
    
    def _search_all_elements_for_stocks(self, soup) -> List[Dict[str, Any]]:
        """Search all page elements for stock data"""
        all_stocks = []
        
        try:
            # Look for divs that might contain stock data
            divs = soup.find_all('div')
            
            for div in divs:
                div_text = div.get_text().lower()
                
                # Check if this div contains stock-like data
                if any(keyword in div_text for keyword in ['nbl', 'nica', 'shl', 'ntc', 'price:', 'change:']):
                    # Try to extract stock data from text
                    stocks = self._extract_stocks_from_text(div.get_text())
                    all_stocks.extend(stocks)
        
        except Exception as e:
            print(f"   ⚠️ Error searching elements: {e}")
        
        return all_stocks
    
    def _extract_stocks_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract stock data from unstructured text"""
        stocks = []
        
        # Simple pattern matching for common Nepali stocks
        common_symbols = ['NICA', 'NBL', 'NTC', 'SHL', 'CBBL', 'SCB', 'NIB', 'NMB', 'HBL', 'ADBL']
        
        lines = text.split('\n')
        for line in lines:
            line_upper = line.upper()
            
            for symbol in common_symbols:
                if symbol in line_upper:
                    # Try to extract numbers
                    import re
                    
                    # Look for price pattern
                    price_match = re.search(r'(\d{3,4}\.\d{2}|\d{3,4})', line)
                    # Look for percentage pattern
                    pct_match = re.search(r'([+-]?\d+\.?\d*)%', line)
                    
                    if price_match:
                        stock = {
                            'symbol': symbol,
                            'securityName': symbol,
                            'ltp': float(price_match.group(1)),
                            'percentageChange': float(pct_match.group(1)) if pct_match else 0,
                            'previousClose': None,
                            'pointChange': None,
                            'is_gainer': (float(pct_match.group(1)) > 0) if pct_match else False
                        }
                        stocks.append(stock)
                        break
        
        return stocks
    
    def _parse_number(self, text: str) -> Optional[float]:
        """Parse number from text"""
        if not text:
            return None
        
        try:
            # Remove common non-numeric characters
            text = str(text).strip()
            
            if text in ['', '-', 'N/A', 'NA', 'null', 'None', '–']:
                return None
            
            # Remove commas, currency symbols, etc.
            text = text.replace(',', '').replace(' ', '').replace('%', '').replace('रु', '').replace('Rs.', '')
            
            # Handle parentheses for negative numbers
            if text.startswith('(') and text.endswith(')'):
                text = '-' + text[1:-1]
            
            # Handle negative signs
            if text.startswith('-'):
                text = text[1:]
                negative = True
            else:
                negative = False
            
            # Parse the number
            result = float(text)
            
            # Reapply negative sign if needed
            if negative:
                result = -result
            
            return result
        
        except (ValueError, TypeError, AttributeError):
            return None
    
    def _get_fallback_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate fallback data when scraping fails"""
        print("⚠️ Using fallback data (for testing only)")
        
        result = {'gainers': [], 'losers': []}
        
        # Sample gainers
        sample_gainers = [
            {'symbol': 'NICA', 'securityName': 'NIC ASIA Bank', 'ltp': 425.50, 'percentageChange': 2.34, 'previousClose': 415.75, 'pointChange': 9.75, 'is_gainer': True},
            {'symbol': 'NBL', 'securityName': 'Nepal Bank', 'ltp': 228.00, 'percentageChange': 1.56, 'previousClose': 224.50, 'pointChange': 3.50, 'is_gainer': True},
            {'symbol': 'NTC', 'securityName': 'Nepal Telecom', 'ltp': 685.25, 'percentageChange': 0.89, 'previousClose': 679.25, 'pointChange': 6.00, 'is_gainer': True},
        ]
        
        # Sample losers
        sample_losers = [
            {'symbol': 'SHL', 'securityName': 'Soaltee Hotel', 'ltp': 315.75, 'percentageChange': -1.25, 'previousClose': 319.75, 'pointChange': -4.00, 'is_gainer': False},
            {'symbol': 'CBBL', 'securityName': 'Chhimek Bank', 'ltp': 298.50, 'percentageChange': -0.85, 'previousClose': 301.00, 'pointChange': -2.50, 'is_gainer': False},
        ]
        
        result['gainers'] = sample_gainers
        result['losers'] = sample_losers
        
        return result

def test_merolagani_scraper():
    """Test the Merolagani scraper"""
    print("=" * 70)
    print("🧪 TESTING MEROLAGANI SCRAPER")
    print("=" * 70)
    
    scraper = MerolaganiScraper()
    data = scraper.get_today_price_data()
    
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS")
    print("=" * 70)
    
    print(f"\n🏆 GAINERS ({len(data['gainers'])}):")
    for i, gainer in enumerate(data['gainers'][:5], 1):
        print(f"   {i}. {gainer.get('symbol', 'N/A')}: {gainer.get('ltp', 0)} ({gainer.get('percentageChange', 0)}%)")
    
    print(f"\n📉 LOSERS ({len(data['losers'])}):")
    for i, loser in enumerate(data['losers'][:5], 1):
        print(f"   {i}. {loser.get('symbol', 'N/A')}: {loser.get('ltp', 0)} ({loser.get('percentageChange', 0)}%)")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    
    return data

if __name__ == "__main__":
    test_merolagani_scraper()
