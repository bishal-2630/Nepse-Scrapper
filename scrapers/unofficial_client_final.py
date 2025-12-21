# scrapers/unofficial_client_final.py
from nepse import NEPSE
import logging
from typing import Dict, List, Optional, Any
from django.utils import timezone

logger = logging.getLogger(__name__)

class UnofficialNepseClientFinal:
    """Final client implementing the combined data strategy."""
    
    def __init__(self):
        self.client = NEPSE()
        self.client.setTLSVerification(False)
        logger.info("NEPSE client initialized with combined data strategy")
    
    def get_security_master_list(self) -> Optional[List[Dict[str, Any]]]:
        """1. MASTER LIST: Get all active securities (544 items)."""
        try:
            data = self.client.getSecurityList()
            if isinstance(data, list):
                logger.info(f"[1/4] Fetched security master list: {len(data)} active items")
                return data
            return None
        except Exception as e:
            logger.error(f"Failed to get security list: {e}")
            return None
    
    def get_todays_price_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """2. PRICE DATA: Get today's gainers and losers with full details."""
        result = {'gainers': [], 'losers': []}
        
        try:
            gainers = self.client.getTopGainers()
            if gainers and isinstance(gainers, list):
                result['gainers'] = gainers
                logger.info(f"[2/4] Fetched {len(gainers)} top gainers")
        except Exception as e:
            logger.error(f"Failed to get top gainers: {e}")
        
        try:
            losers = self.client.getTopLosers()
            if losers and isinstance(losers, list):
                result['losers'] = losers
                logger.info(f"[2/4] Fetched {len(losers)} top losers")
        except Exception as e:
            logger.error(f"Failed to get top losers: {e}")
        
        return result
    
    def get_company_detailed_list(self) -> Optional[List[Dict[str, Any]]]:
        """3. COMPANY INFO: Get detailed company profiles for database."""
        try:
            data = self.client.getCompanyList()
            logger.info(f"[3/4] Fetched company details list: {len(data)} items")
            return data
        except Exception as e:
            logger.error(f"Failed to get company list: {e}")
            return None
    
    def get_individual_security_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """4. INDIVIDUAL LOOKUP: Get details for a specific symbol."""
        try:
            data = self.client.getCompanyDetails(symbol)
            if data:
                logger.debug(f"Fetched details for {symbol}")
                return data
            return None
        except Exception as e:
            logger.error(f"Failed to get details for {symbol}: {e}")
            return None
    
    def get_market_summary_stats(self) -> Optional[List[Dict[str, Any]]]:
        """Get market-wide statistics (total turnover, volume, etc.)."""
        try:
            data = self.client.getSummary()
            if isinstance(data, list):
                logger.info(f"Fetched market summary stats")
                return data
            return None
        except Exception as e:
            logger.error(f"Failed to get market summary: {e}")
            return None

    # Helper to merge data
    def get_combined_daily_data(self) -> Dict[str, Any]:
        """Orchestrates the full data fetching pipeline."""
        current_time = timezone.now()
        
        result = {
            'scrape_timestamp': current_time,
            'scrape_date': current_time.date(),
            'scrape_time': current_time.time(),
            'security_master': self.get_security_master_list(),
            'price_data': self.get_todays_price_data(),
            'company_details': self.get_company_detailed_list(),
            'market_stats': self.get_market_summary_stats()
        }
        return result