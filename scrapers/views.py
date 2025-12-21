# scrapers/views.py - UPDATED VERSION
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Max, Q
from .models import StockData, MarketStatus, Company
from .serializers import StockDataSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .tasks import scrape_24x7
import os
import logging

logger = logging.getLogger(__name__)

class MarketStatusView(APIView):
    """Get current market status"""
    
    def get(self, request):
        # Use Nepal timezone consistently
        import pytz
        nepal_tz = pytz.timezone('Asia/Kathmandu')
        nepal_time = timezone.now().astimezone(nepal_tz)
        today = nepal_time.date()
        
        try:
            market_status = MarketStatus.objects.get(date=today)
            return Response({
                'status': 'success',
                'date': str(today),
                'is_market_open': market_status.is_market_open,
                'last_scraped': market_status.last_scraped,
                'current_time': str(nepal_time),
            })
        except MarketStatus.DoesNotExist:
            return Response({
                'status': 'success',
                'date': str(today),
                'is_market_open': False,
                'last_scraped': None,
                'message': 'No market data available for today',
                'current_time': str(nepal_time),
            })

class LatestStocksView(APIView):
    """Get latest stock data - FIXED VERSION"""
    
    def get(self, request):
        try:
            # Always use Nepal timezone
            import pytz
            nepal_tz = pytz.timezone('Asia/Kathmandu')
            nepal_time = timezone.now().astimezone(nepal_tz)
            today = nepal_time.date()
            
            logger.info(f"[DEPLOYED] LatestStocksView called with Nepal time: {nepal_time}")
            
            # Get ALL data for today, sorted by time
            todays_data = StockData.objects.filter(
                scrape_date=today
            ).select_related('company').order_by('-scrape_time', '-created_at')
            
            logger.info(f"[DEPLOYED] Total records for {today}: {todays_data.count()}")
            
            if not todays_data.exists():
                # If no data for today, get the most recent data from ANY day
                logger.info(f"[DEPLOYED] No data for {today}, getting latest from any day")
                
                # Get the most recent date in the database
                latest_date = StockData.objects.aggregate(
                    latest_date=Max('scrape_date')
                )['latest_date']
                
                if latest_date:
                    latest_data = StockData.objects.filter(
                        scrape_date=latest_date
                    ).select_related('company').order_by('-scrape_time', '-created_at')
                    
                    logger.info(f"[DEPLOYED] Found {latest_data.count()} records from {latest_date}")
                    
                    # Get the latest scrape time for this date
                    latest_scrape_time = latest_data.first().scrape_time if latest_data.exists() else None
                    
                    serializer = StockDataSerializer(latest_data, many=True)
                    
                    # Calculate summary
                    summary = self._calculate_summary(latest_data)
                    
                    return Response({
                        'status': 'success',
                        'date': str(latest_date),
                        'scrape_time': str(latest_scrape_time) if latest_scrape_time else None,
                        'count': len(serializer.data),
                        'summary': summary,
                        'data': serializer.data,
                        'message': f'Showing latest available data from {latest_date}',
                        'note': 'No data available for today yet'
                    })
                else:
                    return Response({
                        'status': 'success',
                        'date': str(today),
                        'count': 0,
                        'data': [],
                        'message': 'No stock data available in database',
                        'timestamp': str(nepal_time)
                    })
            
            # If we have data for today, process it
            # Group by scrape_time to show latest batch
            latest_scrape_time = todays_data.first().scrape_time
            latest_batch = todays_data.filter(scrape_time=latest_scrape_time)
            
            logger.info(f"[DEPLOYED] Latest batch at {latest_scrape_time}: {latest_batch.count()} records")
            
            serializer = StockDataSerializer(latest_batch, many=True)
            summary = self._calculate_summary(latest_batch)
            
            return Response({
                'status': 'success',
                'date': str(today),
                'scrape_time': str(latest_scrape_time),
                'count': len(serializer.data),
                'summary': summary,
                'data': serializer.data,
                'timestamp': str(nepal_time)
            })
            
        except Exception as e:
            logger.error(f"[DEPLOYED] Error in LatestStocksView: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e),
                'timestamp': str(timezone.now())
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _calculate_summary(self, queryset):
        """Calculate summary statistics for the given queryset"""
        if not queryset.exists():
            return {}
        
        # Get stocks with percentage change
        stocks_with_change = []
        for stock in queryset:
            if stock.percentage_change is not None:
                try:
                    change_val = float(stock.percentage_change)
                    stocks_with_change.append((stock, change_val))
                except (ValueError, TypeError):
                    continue
        
        if not stocks_with_change:
            return {}
        
        # Calculate average
        changes = [change for _, change in stocks_with_change]
        avg_change = sum(changes) / len(changes)
        
        # Find top gainer and loser
        top_gainer_stock, top_gainer_val = max(stocks_with_change, key=lambda x: x[1])
        top_loser_stock, top_loser_val = min(stocks_with_change, key=lambda x: x[1])
        
        return {
            'average_percentage_change': round(avg_change, 2),
            'top_gainer': {
                'symbol': top_gainer_stock.symbol,
                'company_name': top_gainer_stock.company.name if top_gainer_stock.company else "Unknown",
                'percentage_change': top_gainer_val,
                'last_traded_price': float(top_gainer_stock.last_traded_price) if top_gainer_stock.last_traded_price else 0
            },
            'top_loser': {
                'symbol': top_loser_stock.symbol,
                'company_name': top_loser_stock.company.name if top_loser_stock.company else "Unknown",
                'percentage_change': top_loser_val,
                'last_traded_price': float(top_loser_stock.last_traded_price) if top_loser_stock.last_traded_price else 0
            }
        }

class TopGainersView(APIView):
    """Get top 10 gainers - FIXED VERSION"""
    
    def get(self, request):
        try:
            # Use Nepal timezone
            import pytz
            nepal_tz = pytz.timezone('Asia/Kathmandu')
            nepal_time = timezone.now().astimezone(nepal_tz)
            today = nepal_time.date()
            
            # Get latest data for today
            todays_data = StockData.objects.filter(
                scrape_date=today
            ).select_related('company').order_by('-scrape_time')
            
            if not todays_data.exists():
                # Fallback to latest date
                latest_date = StockData.objects.aggregate(
                    latest_date=Max('scrape_date')
                )['latest_date']
                
                if not latest_date:
                    return Response({
                        'status': 'success',
                        'date': str(today),
                        'count': 0,
                        'data': [],
                        'message': 'No data available'
                    })
                
                todays_data = StockData.objects.filter(
                    scrape_date=latest_date
                ).select_related('company').order_by('-scrape_time')
                today = latest_date
            
            # Get latest scrape time
            latest_scrape_time = todays_data.first().scrape_time if todays_data.exists() else None
            
            # Get top gainers (positive change)
            top_gainers = StockData.objects.filter(
                scrape_date=today,
                scrape_time=latest_scrape_time,
                percentage_change__gt=0
            ).select_related('company').order_by('-percentage_change')[:10]
            
            serializer = StockDataSerializer(top_gainers, many=True)
            
            return Response({
                'status': 'success',
                'date': str(today),
                'scrape_time': str(latest_scrape_time) if latest_scrape_time else None,
                'count': len(serializer.data),
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error in TopGainersView: {e}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TopLosersView(APIView):
    """Get top 10 losers - FIXED VERSION"""
    
    def get(self, request):
        try:
            # Use Nepal timezone
            import pytz
            nepal_tz = pytz.timezone('Asia/Kathmandu')
            nepal_time = timezone.now().astimezone(nepal_tz)
            today = nepal_time.date()
            
            # Get latest data for today
            todays_data = StockData.objects.filter(
                scrape_date=today
            ).select_related('company').order_by('-scrape_time')
            
            if not todays_data.exists():
                # Fallback to latest date
                latest_date = StockData.objects.aggregate(
                    latest_date=Max('scrape_date')
                )['latest_date']
                
                if not latest_date:
                    return Response({
                        'status': 'success',
                        'date': str(today),
                        'count': 0,
                        'data': [],
                        'message': 'No data available'
                    })
                
                todays_data = StockData.objects.filter(
                    scrape_date=latest_date
                ).select_related('company').order_by('-scrape_time')
                today = latest_date
            
            # Get latest scrape time
            latest_scrape_time = todays_data.first().scrape_time if todays_data.exists() else None
            
            # Get top losers (negative change)
            top_losers = StockData.objects.filter(
                scrape_date=today,
                scrape_time=latest_scrape_time,
                percentage_change__lt=0
            ).select_related('company').order_by('percentage_change')[:10]
            
            serializer = StockDataSerializer(top_losers, many=True)
            
            return Response({
                'status': 'success',
                'date': str(today),
                'scrape_time': str(latest_scrape_time) if latest_scrape_time else None,
                'count': len(serializer.data),
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error in TopLosersView: {e}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
def cron_simple_scrape(request):
    """Simple cron endpoint that forces scraping"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        logger.info(f"=== FORCED SCRAPING triggered at {timezone.now()} ===")
        
        # Force scraping synchronously
        from .data_processor import NepseDataProcessor24x7
        processor = NepseDataProcessor24x7()
        
        # Force update companies first
        companies_created, companies_updated = processor.update_companies()
        
        # Then scrape data
        result = processor.execute_24x7_scraping()
        
        # Log detailed result
        logger.info(f"Forced scraping result: {result}")
        
        return JsonResponse({
            'status': 'success',
            'companies_updated': f"{companies_created} created, {companies_updated} updated",
            'records_saved': result.get('records_saved', 0),
            'data_source': result.get('data_source_used', 'unknown'),
            'message': 'Forced scraping completed',
            'timestamp': str(timezone.now())
        })
        
    except Exception as e:
        logger.error(f"Forced scraping failed: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': str(timezone.now())
        }, status=500)

class CronTestView(APIView):
    """Test endpoint for cron job"""
    def get(self, request):
        # Check database status
        total_stocks = StockData.objects.count()
        total_companies = Company.objects.count()
        latest_date = StockData.objects.aggregate(
            latest_date=Max('scrape_date')
        )['latest_date']
        
        return Response({
            'status': 'success',
            'message': 'API is working',
            'database_status': {
                'total_stock_records': total_stocks,
                'total_companies': total_companies,
                'latest_data_date': str(latest_date) if latest_date else 'No data'
            },
            'endpoints': {
                'latest_stocks': '/api/stocks/latest/',
                'top_gainers': '/api/stocks/top-gainers/',
                'top_losers': '/api/stocks/top-losers/',
                'force_scrape': '/api/cron/simple/'
            },
            'timestamp': timezone.now().isoformat()
        })