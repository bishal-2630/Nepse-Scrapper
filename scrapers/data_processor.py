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
    """24/7 Data processor - ONLY processes available data"""
    
    def __init__(self):
        self.client = UnofficialNepseClientFinal()
        self.current_time = timezone.localtime()
        self.scrape_date = self.current_time.date()
        self.scrape_time = self.current_time.time()
        
        # Nepal market hours (Sunday-Thursday, 11:00-15:00)
        self.market_open_time = time_obj(11, 0)
        self.market_close_time = time_obj(15, 0)
        
        # Determine if today is a trading day (0=Monday, 6=Sunday)
        self.weekday = self.current_time.weekday()
        self.is_trading_day = self.weekday in [6, 0, 1, 2, 3]  # Sun-Thu
        
        # Determine current market session
        self.market_session = self._get_market_session()
    
    def _get_market_session(self) -> str:
        """Determine current market session"""
        if not self.is_trading_day:
            return 'after_hours'
        
        if self.scrape_time < self.market_open_time:
            return 'pre_open'
        elif self.market_open_time <= self.scrape_time <= self.market_close_time:
            return 'regular'
        else:
            return 'post_close'
    
    def _get_data_source_type(self) -> str:
        """Determine what type of data to fetch"""
        session = self.market_session
        
        if session == 'regular':
            return 'live'
        elif session == 'post_close':
            # First 2 hours after close, try to get closing data
            close_plus_2 = datetime.combine(self.scrape_date, self.market_close_time) + timedelta(hours=2)
            if self.current_time < timezone.make_aware(close_plus_2):
                return 'closing'
            else:
                return 'historical'
        else:  # pre_open, after_hours, or non-trading day
            return 'historical'
    
    def update_companies(self) -> Tuple[int, int]:
        """Update company list - runs daily"""
        companies_data = self.client.get_company_detailed_list()
        if not companies_data:
            logger.warning("No company data received")
            return 0, 0
        
        created_count = 0
        updated_count = 0
        
        for company_data in companies_data:
            try:
                symbol = company_data.get('symbol', '').strip().upper()
                name = company_data.get('companyName') or company_data.get('securityName', '').strip()
                
                if not symbol or not name:
                    continue
                
                company, created = Company.objects.update_or_create(
                    symbol=symbol,
                    defaults={
                        'name': name,
                        'sector': company_data.get('sectorName', ''),
                        'listed_shares': company_data.get('totalListedShares', 0) or 0,
                        'is_active': company_data.get('status', '').upper() == 'ACTIVE',
                    }
                )
                
                if created:
                    created_count += 1
                    logger.debug(f"Created company: {symbol}")
                else:
                    updated_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing company {company_data.get('symbol')}: {e}")
                continue
        
        logger.info(f"Company update: {created_count} created, {updated_count} updated")
        return created_count, updated_count
    
    def _save_stock_record(self, stock_item: Dict, data_source: str, 
                          custom_time: time_obj = None) -> bool:
        """Save individual stock record - ONLY available data"""
        try:
            symbol = stock_item.get('symbol', '').strip().upper()
            if not symbol:
                return False
            
            # Get or create company
            company, created = Company.objects.get_or_create(
                symbol=symbol,
                defaults={
                    'name': stock_item.get('securityName', symbol),
                    'is_active': True
                }
            )
            
            # Update company name if it exists
            if not created:
                new_name = stock_item.get('securityName')
                if new_name and company.name != new_name:
                    company.name = new_name
                    company.save()
            
            # Determine scrape time
            scrape_time = custom_time or self.scrape_time
            
            # Check for existing record
            existing = StockData.objects.filter(
                company=company,
                symbol=symbol,
                scrape_date=self.scrape_date,
                scrape_time=scrape_time,
                data_source=data_source
            ).exists()
            
            if existing:
                logger.debug(f"Duplicate record skipped: {symbol} {self.scrape_date} {scrape_time}")
                return False
            
            # ✅ ONLY parse data we actually get from API
            stock_record = StockData(
                company=company,
                symbol=symbol,
                # ✅ ACTUAL DATA FROM API:
                close_price=self._parse_decimal(stock_item.get('cp')),
                last_traded_price=self._parse_decimal(stock_item.get('ltp')),
                previous_close=self._parse_decimal(stock_item.get('previousClose')),
                difference=self._parse_decimal(stock_item.get('pointChange')),
                percentage_change=self._parse_decimal(stock_item.get('percentageChange')),
                
                # Metadata
                scrape_date=self.scrape_date,
                scrape_time=scrape_time,
                data_source=data_source,
                is_closing_data=(data_source in ['closing', 'historical'])
            )
            
            stock_record.save()
            return True
            
        except Exception as e:
            logger.error(f"Error saving stock record for {stock_item.get('symbol')}: {e}")
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