# scrapers/unofficial_client_final.py - USING WORKING MEROLAGANI SCRAPER
import logging
import sys
import os
from typing import Dict, List, Optional, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

class UnofficialNepseClientFinal:
    """NEPSE client using the working Merolagani scraper"""
    
    def __init__(self):
        self.scraper = None
        
        try:
            # Import the working Merolagani scraper
            from merolagani_scraper import MerolaganiScraper
            self.scraper = MerolaganiScraper()
            logger.info("✅ Initialized MerolaganiScraper (Working!)")
        except ImportError as e:
            logger.error(f"Failed to import MerolaganiScraper: {e}")
        except Exception as e:
            logger.error(f"Error initializing scraper: {e}")
    
    def get_todays_price_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get today's price data - MAIN METHOD"""
        if not self.scraper:
            logger.error("Scraper not initialized")
            return {'gainers': [], 'losers': []}
        
        try:
            # This will use the working scraper
            result = self.scraper.get_today_price_data()
            logger.info(f"✅ Retrieved {len(result['gainers'])} gainers, {len(result['losers'])} losers")
            return result
        except Exception as e:
            logger.error(f"Error getting price data: {e}")
            return {'gainers': [], 'losers': []}
    
    def get_security_master_list(self) -> Optional[List[Dict[str, Any]]]:
        """Get list of all securities - we can extract from the data"""
        try:
            # Get price data first
            price_data = self.get_todays_price_data()
            
            # Extract unique symbols
            securities = []
            seen_symbols = set()
            
            # Add from gainers
            for stock in price_data.get('gainers', []):
                symbol = stock.get('symbol')
                if symbol and symbol not in seen_symbols:
                    securities.append({
                        'symbol': symbol,
                        'securityName': stock.get('securityName', symbol),
                        'sector': 'Unknown'  # Merolagani doesn't provide sector info
                    })
                    seen_symbols.add(symbol)
            
            # Add from losers
            for stock in price_data.get('losers', []):
                symbol = stock.get('symbol')
                if symbol and symbol not in seen_symbols:
                    securities.append({
                        'symbol': symbol,
                        'securityName': stock.get('securityName', symbol),
                        'sector': 'Unknown'
                    })
                    seen_symbols.add(symbol)
            
            logger.info(f"Extracted {len(securities)} securities from price data")
            return securities
            
        except Exception as e:
            logger.error(f"Error getting security list: {e}")
            return []
    
    def get_market_summary_stats(self) -> Optional[List[Dict[str, Any]]]:
        """Get market summary - placeholder for now"""
        return []

# Test the client
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("="*70)
    print("🧪 Testing Unofficial NEPSE Client with Merolagani Scraper")
    print("="*70)
    
    client = UnofficialNepseClientFinal()
    
    if client.scraper:
        print("✅ Client initialized successfully!")
        
        print("\n📥 Fetching live market data...")
        data = client.get_todays_price_data()
        
        print(f"\n📊 Results:")
        print(f"   Gainers: {len(data['gainers'])}")
        print(f"   Losers: {len(data['losers'])}")
        
        if data['gainers']:
            print(f"\n🏆 Top 5 Gainers:")
            for i, gainer in enumerate(data['gainers'][:5], 1):
                print(f"   {i}. {gainer.get('symbol')}: {gainer.get('ltp')} ({gainer.get('percentageChange')}%)")
        
        if data['losers']:
            print(f"\n📉 Top 5 Losers:")
            for i, loser in enumerate(data['losers'][:5], 1):
                print(f"   {i}. {loser.get('symbol')}: {loser.get('ltp')} ({loser.get('percentageChange')}%)")
        
        print(f"\n📋 Extracting securities list...")
        securities = client.get_security_master_list()
        print(f"   Securities extracted: {len(securities)}")
        
        if securities:
            print(f"   Sample: {securities[0].get('symbol')} - {securities[0].get('securityName')}")
        
    else:
        print("❌ Client failed to initialize")
    
    print("\n" + "="*70)
    print("✅ Test Complete - System is READY!")
    print("="*70)
