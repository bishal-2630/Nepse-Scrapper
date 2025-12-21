# scrapers/tasks.py - CORRECTED VERSION
from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Max, Min, Avg, Sum
from datetime import timedelta, datetime, time as time_obj
import logging
from .data_processor import NepseDataProcessor24x7
from .models import MarketStatus, StockData, Company

logger = logging.getLogger(__name__)

@shared_task
def scrape_24x7():
    """Main 24/7 scraping task - runs every 30 minutes"""
    logger.info("=== Starting 24/7 Scraping Task ===")
    
    try:
        processor = NepseDataProcessor24x7()
        result = processor.execute_24x7_scraping()
        
        # Log the result
        success = result.get('success', False)
        records = result.get('records_saved', 0)
        data_source = result.get('data_source_used', 'unknown')
        
        if success:
            logger.info(f"✓ 24/7 scraping SUCCESS: {records} records via {data_source}")
        else:
            logger.warning(f"⚠ 24/7 scraping partial: {result.get('message', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"✗ 24/7 scraping FAILED: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': str(timezone.now())
        }

@shared_task
def force_closing_data():
    """Force scraping of closing data (run at 3:30 PM daily)"""
    logger.info("Forcing closing data scrape...")
    
    try:
        processor = NepseDataProcessor24x7()
        result = processor.execute_24x7_scraping()
        
        if result.get('success'):
            logger.info(f"Closing data scraped: {result.get('records_saved', 0)} records")
        else:
            logger.warning(f"Closing data failed: {result.get('message')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Force closing data failed: {e}")
        return {'status': 'error', 'error': str(e)}

@shared_task
def daily_maintenance():
    """Daily maintenance tasks - DO NOT DELETE HISTORICAL DATA"""
    logger.info("Running daily maintenance (preserving all historical data)...")
    
    try:
        today = timezone.now().date()
        
        # 1. ENSURE MARKET STATUS EXISTS FOR TODAY
        market_status, created = MarketStatus.objects.get_or_create(
            date=today,
            defaults={
                'is_market_open': False,
                'last_scraped': timezone.now(),
                'total_turnover': 0,
                'total_volume': 0,
                'total_transactions': 0
            }
        )
        
        # 2. CALCULATE STATISTICS (NOT DELETE DATA)
        stats = {}
        
        # Total data statistics
        stats['total_companies'] = Company.objects.count()
        stats['total_stock_records'] = StockData.objects.count()
        
        # Today's data
        today_data = StockData.objects.filter(scrape_date=today)
        stats['today_records'] = today_data.count()
        
        # Check for data gaps
        if stats['today_records'] > 0:
            # Get unique symbols for today
            today_symbols = today_data.values('symbol').distinct().count()
            stats['today_symbols'] = today_symbols
            
            # Get latest scrape time
            latest_scrape = today_data.aggregate(Max('scrape_time'))['scrape_time__max']
            stats['latest_scrape_time'] = str(latest_scrape) if latest_scrape else None
            
            # Calculate average values
            avg_change = today_data.filter(percentage_change__isnull=False).aggregate(
                Avg('percentage_change')
            )['percentage_change__avg']
            stats['avg_percentage_change'] = float(avg_change) if avg_change else 0
            
            # Find top gainer/loser
            if today_symbols > 0:
                top_gainer = today_data.filter(
                    percentage_change__isnull=False
                ).order_by('-percentage_change').first()
                
                top_loser = today_data.filter(
                    percentage_change__isnull=False
                ).order_by('percentage_change').first()
                
                if top_gainer:
                    stats['top_gainer'] = {
                        'symbol': top_gainer.symbol,
                        'change': float(top_gainer.percentage_change) if top_gainer.percentage_change else 0
                    }
                
                if top_loser:
                    stats['top_loser'] = {
                        'symbol': top_loser.symbol,
                        'change': float(top_loser.percentage_change) if top_loser.percentage_change else 0
                    }
        
        # 3. CHECK DATA COMPLETENESS (FOR LOGGING ONLY)
        all_companies = Company.objects.filter(is_active=True).count()
        
        if all_companies > 0 and stats['today_records'] > 0:
            coverage_percentage = (stats['today_symbols'] / all_companies) * 100
            stats['data_coverage'] = f"{coverage_percentage:.1f}%"
            
            if coverage_percentage < 50:
                logger.warning(f"Low data coverage: {coverage_percentage:.1f}% of active companies")
        
        # 4. CREATE BACKUP SUMMARY (OPTIONAL)
        # This creates a summary without deleting anything
        yesterday = today - timedelta(days=1)
        yesterday_summary = StockData.objects.filter(
            scrape_date=yesterday,
            data_source='closing'  # Look for closing data
        ).order_by('-scrape_time').first()
        
        if yesterday_summary:
            stats['yesterday_summary_available'] = True
            stats['yesterday_date'] = str(yesterday)
            stats['yesterday_records'] = StockData.objects.filter(scrape_date=yesterday).count()
        else:
            stats['yesterday_summary_available'] = False
        
        # 5. UPDATE MARKET STATUS WITH STATS
        if not market_status.last_scraped or (timezone.now() - market_status.last_scraped).seconds > 3600:
            market_status.last_scraped = timezone.now()
            market_status.save()
        
        logger.info(f"Daily maintenance complete. Stats: {stats}")
        
        return {
            'status': 'success',
            'action': 'maintenance_only',
            'data_preserved': True,
            'stats': stats,
            'timestamp': str(timezone.now())
        }
        
    except Exception as e:
        logger.error(f"Daily maintenance failed: {e}", exc_info=True)
        return {'status': 'error', 'error': str(e)}