# scrapers/data_processor.py
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta, time as time_obj
from typing import Dict, List, Optional, Tuple, Any
from .models import Company, StockData, MarketStatus
from .unofficial_client_final import UnofficialNepseClientFinal
import logging

logger = logging.getLogger(__name__)

class NepseDataProcessor24x7:
    """24/7 Data processor - WITH FIXES FOR DEPLOYMENT"""
    
    def execute_24x7_scraping(self) -> Dict[str, Any]:
        """Main method: intelligent 24/7 scraping - WITH DEPLOYMENT FIXES"""
        logger.info(f"[DEPLOYED] Starting 24/7 scraping for {self.scrape_date} {self.scrape_time}")
        
        # ALWAYS update companies first
        companies_created, companies_updated = self.update_companies()
        logger.info(f"[DEPLOYED] Company update: {companies_created} created, {companies_updated} updated")
        
        # Try to get price data
        price_data = None
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"[DEPLOYED] Attempt {attempt + 1}/{max_attempts} to get price data")
                price_data = self.client.get_todays_price_data()
                
                if price_data and (price_data.get('gainers') or price_data.get('losers')):
                    logger.info(f"[DEPLOYED] Got price data with {len(price_data.get('gainers', []))} gainers and {len(price_data.get('losers', []))} losers")
                    break
                else:
                    logger.warning(f"[DEPLOYED] No price data received, attempt {attempt + 1}")
                    
            except Exception as e:
                logger.error(f"[DEPLOYED] Error getting price data (attempt {attempt + 1}): {e}")
            
            if attempt < max_attempts - 1:
                import time
                time.sleep(2)  # Wait before retry
        
        if not price_data:
            logger.error("[DEPLOYED] Failed to get any price data after all attempts")
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
        logger.info(f"[DEPLOYED] Processing {len(gainers)} gainers")
        
        for stock_item in gainers:
            try:
                saved = self._save_stock_record(stock_item, data_source, scrape_time)
                if saved:
                    saved_count += 1
            except Exception as e:
                logger.error(f"[DEPLOYED] Error saving gainer {stock_item.get('symbol')}: {e}")
        
        # Process losers
        losers = price_data.get('losers', [])
        logger.info(f"[DEPLOYED] Processing {len(losers)} losers")
        
        for stock_item in losers:
            try:
                saved = self._save_stock_record(stock_item, data_source, scrape_time)
                if saved:
                    saved_count += 1
            except Exception as e:
                logger.error(f"[DEPLOYED] Error saving loser {stock_item.get('symbol')}: {e}")
        
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
        
        logger.info(f"[DEPLOYED] Scraping completed: {result}")
        return result
    
    def _save_stock_record(self, stock_item: Dict, data_source: str, 
                          custom_time: time_obj = None) -> bool:
        """Save individual stock record - ENHANCED FOR DEPLOYMENT"""
        try:
            symbol = stock_item.get('symbol', '').strip().upper()
            if not symbol:
                logger.warning("[DEPLOYED] No symbol in stock item")
                return False
            
            # DEBUG: Log what we're receiving
            logger.debug(f"[DEPLOYED] Processing symbol: {symbol}, data: {stock_item}")
            
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
                logger.debug(f"[DEPLOYED] Duplicate record exists for {symbol} {self.scrape_date} {scrape_time}")
                return False
            
            # Extract and clean data
            close_price = self._parse_decimal(stock_item.get('cp'))
            last_traded_price = self._parse_decimal(stock_item.get('ltp'))
            previous_close = self._parse_decimal(stock_item.get('previousClose'))
            difference = self._parse_decimal(stock_item.get('pointChange'))
            percentage_change = self._parse_decimal(stock_item.get('percentageChange'))
            
            # Log what we're saving
            logger.debug(f"[DEPLOYED] Saving {symbol}: LTP={last_traded_price}, Change={percentage_change}")
            
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
            logger.info(f"[DEPLOYED] ✅ Saved record for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"[DEPLOYED] ❌ Error saving {stock_item.get('symbol')}: {e}", exc_info=True)
            return False
    
    def scrape_live_market_data(self) -> Dict[str, Any]:
        """Scrape live data during market hours"""
        logger.info(f"Scraping LIVE market data for {self.scrape_date} {self.scrape_time}")
        
        price_data = self.client.get_todays_price_data()
        if not price_data:
            logger.warning("No live price data received")
            return {'success': False, 'message': 'No live data'}
        
        saved_count = 0
        
        # Process both gainers and losers
        for list_type in ['gainers', 'losers']:
            stock_list = price_data.get(list_type, [])
            
            for stock_item in stock_list:
                try:
                    saved = self._save_stock_record(stock_item, 'live')
                    if saved:
                        saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving {list_type} {stock_item.get('symbol')}: {e}")
        
        logger.info(f"Live scraping: {saved_count} records saved")
        return {
            'success': saved_count > 0,
            'records_saved': saved_count,
            'data_source': 'live',
            'session': 'regular'
        }
    
    def execute_24x7_scraping(self) -> Dict[str, Any]:
        """Main method: intelligent 24/7 scraping"""
        logger.info(f"Starting 24/7 scraping for {self.scrape_date} {self.scrape_time}")
        logger.info(f"Market session: {self.market_session}, Trading day: {self.is_trading_day}")
        
        data_source = self._get_data_source_type()
        logger.info(f"Data source strategy: {data_source}")
        
        # Always update companies daily (but not too frequently)
        last_company_update = Company.objects.aggregate(models.Max('updated_at'))['updated_at__max']
        update_companies = True
        
        if last_company_update:
            hours_since_update = (timezone.now() - last_company_update).total_seconds() / 3600
            update_companies = hours_since_update > 6
        
        if update_companies:
            self.update_companies()
        
        # Execute based on data source
        if data_source == 'live':
            result = self.scrape_live_market_data()
        else:  # closing or historical
            result = self._scrape_non_live_data(data_source)
        
        # Update market status
        self._update_market_status(result.get('success', False))
        
        # Add metadata
        result.update({
            'timestamp': str(timezone.now()),
            'scrape_date': str(self.scrape_date),
            'scrape_time': str(self.scrape_time),
            'market_session': self.market_session,
            'is_trading_day': self.is_trading_day,
            'data_source_used': data_source
        })
        
        logger.info(f"24/7 scraping completed: {result.get('success', False)}")
        return result
    
    def _scrape_non_live_data(self, data_source: str) -> Dict[str, Any]:
        """Scrape closing or historical data"""
        logger.info(f"Scraping {data_source.upper()} data for {self.scrape_date}")
        
        price_data = self.client.get_todays_price_data()
        if not price_data:
            return {'success': False, 'message': f'No {data_source} data available'}
        
        saved_count = 0
        # Use a standard time for non-live data (3:30 PM for closing, 4:00 PM for historical)
        scrape_time = time_obj(15, 30) if data_source == 'closing' else time_obj(16, 0)
        
        for list_type in ['gainers', 'losers']:
            stock_list = price_data.get(list_type, [])
            
            for stock_item in stock_list:
                try:
                    saved = self._save_stock_record(stock_item, data_source, scrape_time)
                    if saved:
                        saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving {data_source} {list_type}: {e}")
        
        return {
            'success': saved_count > 0,
            'records_saved': saved_count,
            'data_source': data_source,
            'message': f'{saved_count} {data_source} records saved'
        }
    
    def _update_market_status(self, has_data: bool) -> bool:
        """Update market status in database"""
        try:
            market_status, created = MarketStatus.objects.update_or_create(
                date=self.scrape_date,
                defaults={
                    'is_market_open': (self.market_session == 'regular' and has_data),
                    'last_scraped': timezone.now(),
                    'market_close_time': self.market_close_time if self.market_session != 'regular' else None
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error updating market status: {e}")
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