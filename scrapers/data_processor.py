# scrapers/data_processor.py
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta, time as time_obj
from typing import Dict, List, Optional, Tuple, Any
from .models import Company, StockData, MarketStatus
from .unofficial_client_final import UnofficialNepseClientFinal
import logging
import pytz

logger = logging.getLogger(__name__)

class NepseDataProcessor24x7:
    """24/7 Data processor - COMPLETE VERSION"""
    
    def __init__(self):
        self.client = UnofficialNepseClientFinal()
        nepal_tz = pytz.timezone('Asia/Kathmandu')
        self.nepal_now = timezone.now().astimezone(nepal_tz)
        self.scrape_date = self.nepal_now.date()
        self.scrape_time = self.nepal_now.time()
        
        # Determine market session
        self.market_session = self._determine_market_session()
        self.is_trading_day = self._is_trading_day()
        
        logger.info(f"Initialized processor for {self.scrape_date} {self.scrape_time}")
        logger.info(f"Market session: {self.market_session}, Trading day: {self.is_trading_day}")
    
    def _determine_market_session(self):
        """Determine if we're in market hours"""
        current_hour = self.nepal_now.hour
        current_minute = self.nepal_now.minute
        
        # Market hours: 11:00 AM to 3:00 PM Nepal time (Sunday-Thursday)
        if self.nepal_now.weekday() in [6, 0, 1, 2, 3]:  # Sun-Thu
            if 11 <= current_hour < 15:
                return 'regular'
            elif current_hour >= 15:
                return 'after_hours'
            else:
                return 'pre_market'
        else:
            return 'weekend'
    
    def _is_trading_day(self):
        """Check if today is a trading day (Sunday-Thursday)"""
        # Sunday=6, Monday=0, Tuesday=1, Wednesday=2, Thursday=3
        return self.nepal_now.weekday() in [6, 0, 1, 2, 3]
    
    def update_companies(self):
        """Update company list from master security list"""
        try:
            companies_created = 0
            companies_updated = 0
            
            security_list = self.client.get_security_master_list()
            if not security_list:
                logger.warning("No security list received")
                return 0, 0
            
            for security in security_list:
                try:
                    symbol = security.get('symbol', '').strip().upper()
                    name = security.get('securityName', symbol)
                    
                    if not symbol:
                        continue
                    
                    company, created = Company.objects.update_or_create(
                        symbol=symbol,
                        defaults={
                            'name': name,
                            'is_active': True
                        }
                    )
                    
                    if created:
                        companies_created += 1
                    else:
                        companies_updated += 1
                        
                except Exception as e:
                    logger.error(f"Error processing security {security.get('symbol')}: {e}")
                    continue
            
            logger.info(f"Company update: {companies_created} created, {companies_updated} updated")
            return companies_created, companies_updated
            
        except Exception as e:
            logger.error(f"Error updating companies: {e}", exc_info=True)
            return 0, 0
    
    def execute_24x7_scraping(self) -> Dict[str, Any]:
        """Main method: intelligent 24/7 scraping"""
        logger.info(f"Starting 24/7 scraping for {self.scrape_date} {self.scrape_time}")
        
        # ALWAYS update companies first
        companies_created, companies_updated = self.update_companies()
        logger.info(f"Company update: {companies_created} created, {companies_updated} updated")
        
        # Try to get price data
        price_data = None
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"Attempt {attempt + 1}/{max_attempts} to get price data")
                price_data = self.client.get_todays_price_data()
                
                if price_data and (price_data.get('gainers') or price_data.get('losers')):
                    logger.info(f"Got price data with {len(price_data.get('gainers', []))} gainers and {len(price_data.get('losers', []))} losers")
                    break
                else:
                    logger.warning(f"No price data received, attempt {attempt + 1}")
                    
            except Exception as e:
                logger.error(f"Error getting price data (attempt {attempt + 1}): {e}")
            
            if attempt < max_attempts - 1:
                import time
                time.sleep(2)  # Wait before retry
        
        if not price_data:
            logger.error("Failed to get any price data after all attempts")
            return {
                'success': False,
                'message': 'No price data available',
                'companies_updated': f"{companies_created} created, {companies_updated} updated",
                'records_saved': 0
            }
        
        # Process data
        saved_count = 0
        scrape_time = self.scrape_time
        
        # Determine data source
        if self.market_session == 'regular':
            data_source = 'live'
        else:
            data_source = 'historical'
            # Use a fixed time for non-live data
            scrape_time = time_obj(15, 30)
        
        # Process gainers
        gainers = price_data.get('gainers', [])
        logger.info(f"Processing {len(gainers)} gainers")
        
        for stock_item in gainers:
            try:
                saved = self._save_stock_record(stock_item, data_source, scrape_time)
                if saved:
                    saved_count += 1
            except Exception as e:
                logger.error(f"Error saving gainer {stock_item.get('symbol')}: {e}")
        
        # Process losers
        losers = price_data.get('losers', [])
        logger.info(f"Processing {len(losers)} losers")
        
        for stock_item in losers:
            try:
                saved = self._save_stock_record(stock_item, data_source, scrape_time)
                if saved:
                    saved_count += 1
            except Exception as e:
                logger.error(f"Error saving loser {stock_item.get('symbol')}: {e}")
        
        # Update market status
        self._update_market_status(saved_count > 0)
        
        result = {
            'success': saved_count > 0,
            'companies_updated': f"{companies_created} created, {companies_updated} updated",
            'records_saved': saved_count,
            'data_source_used': data_source,
            'market_session': self.market_session,
            'is_trading_day': self.is_trading_day,
            'timestamp': str(timezone.now()),
            'scrape_date': str(self.scrape_date),
            'scrape_time': str(self.scrape_time),
            'message': f'Scraped {saved_count} records via {data_source}'
        }
        
        logger.info(f"Scraping completed: {result}")
        return result
    
    def _save_stock_record(self, stock_item: Dict, data_source: str, 
                          custom_time: time_obj = None) -> bool:
        """Save individual stock record"""
        try:
            symbol = stock_item.get('symbol', '').strip().upper()
            if not symbol:
                logger.warning("No symbol in stock item")
                return False
            
            # DEBUG: Log what we're receiving
            logger.debug(f"Processing symbol: {symbol}, data: {stock_item}")
            
            # Get or create company
            company, created = Company.objects.get_or_create(
                symbol=symbol,
                defaults={
                    'name': stock_item.get('securityName', symbol),
                    'is_active': True
                }
            )
            
            # Update company info if it exists
            if not created:
                new_name = stock_item.get('securityName')
                if new_name and company.name != new_name:
                    company.name = new_name
                    company.save()
            
            # Determine scrape time
            scrape_time = custom_time or self.scrape_time
            
            # Check for existing record (with more flexible matching)
            existing = StockData.objects.filter(
                company=company,
                scrape_date=self.scrape_date,
                scrape_time=scrape_time,
                data_source=data_source
            ).exists()
            
            if existing:
                logger.debug(f"Duplicate record exists for {symbol} {self.scrape_date} {scrape_time}")
                return False
            
            # Extract and clean data
            close_price = self._parse_decimal(stock_item.get('cp'))
            last_traded_price = self._parse_decimal(stock_item.get('ltp'))
            previous_close = self._parse_decimal(stock_item.get('previousClose'))
            difference = self._parse_decimal(stock_item.get('pointChange'))
            percentage_change = self._parse_decimal(stock_item.get('percentageChange'))
            
            # Log what we're saving
            logger.debug(f"Saving {symbol}: LTP={last_traded_price}, Change={percentage_change}")
            
            # Create and save record
            stock_record = StockData(
                company=company,
                symbol=symbol,
                close_price=close_price,
                last_traded_price=last_traded_price,
                previous_close=previous_close,
                difference=difference,
                percentage_change=percentage_change,
                scrape_date=self.scrape_date,
                scrape_time=scrape_time,
                data_source=data_source,
                is_closing_data=(data_source in ['closing', 'historical'])
            )
            
            stock_record.save()
            logger.info(f"✅ Saved record for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving {stock_item.get('symbol')}: {e}", exc_info=True)
            return False
    
    def _parse_decimal(self, value):
        """Safely parse decimal values"""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _update_market_status(self, has_data: bool) -> bool:
        """Update market status in database"""
        try:
            market_status, created = MarketStatus.objects.update_or_create(
                date=self.scrape_date,
                defaults={
                    'is_market_open': (self.market_session == 'regular' and has_data),
                    'last_scraped': timezone.now(),
                }
            )
            logger.info(f"Market status updated: {'OPEN' if market_status.is_market_open else 'CLOSED'}")
            return True
        except Exception as e:
            logger.error(f"Error updating market status: {e}")
            return False
    
    # Add to NepseDataProcessor24x7 class
def execute_scraping(self):
    """Simplified main scraping method"""
    try:
        # Always update companies first
        companies_created, companies_updated = self.update_companies()
        
        # Get price data
        price_data = self.client.get_todays_price_data()
        
        if not price_data or (not price_data.get('gainers') and not price_data.get('losers')):
            logger.warning("No price data available")
            return {
                'success': False,
                'message': 'No price data available',
                'companies_updated': f"{companies_created} created, {companies_updated} updated"
            }
        
        # Process and save data
        saved_count = 0
        data_source = 'live' if self.market_session == 'regular' else 'historical'
        
        # Process all stocks
        all_stocks = price_data.get('gainers', []) + price_data.get('losers', [])
        
        for stock_item in all_stocks:
            try:
                saved = self._save_stock_record(stock_item, data_source, self.scrape_time)
                if saved:
                    saved_count += 1
            except Exception as e:
                logger.error(f"Error saving {stock_item.get('symbol')}: {e}")
        
        # Update market status
        self._update_market_status(saved_count > 0)
        
        return {
            'success': saved_count > 0,
            'records_saved': saved_count,
            'companies_updated': f"{companies_created} created, {companies_updated} updated",
            'data_source': data_source,
            'market_session': self.market_session,
            'timestamp': str(timezone.now())
        }
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'timestamp': str(timezone.now())
        }