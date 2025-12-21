
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

class HomeView(APIView):
    """Home view with API documentation"""
    
    def get(self, request):
        base_url = request.build_absolute_uri('/')
        return Response({
            'message': 'NEPSE Scraper API',
            'endpoints': {
                'market_status': f'{base_url}api/status/',
                'latest_stocks': f'{base_url}api/stocks/latest/',
                'top_gainers': f'{base_url}api/stocks/top-gainers/',
                'top_losers': f'{base_url}api/stocks/top-losers/',
                'api_documentation': f'{base_url}swagger/',
            },
            'description': 'Automated NEPSE stock market data scraper',
            'market_hours': 'Sunday-Thursday, 11:00 AM - 3:00 PM (Nepal Time)',
            'data_refresh': 'Every 5 minutes during market hours',
        })

class MarketStatusView(APIView):
    """Get current market status"""
    
    def get(self, request):
        today = timezone.now().date()
        
        try:
            market_status = MarketStatus.objects.get(date=today)
            return Response({
                'status': 'success',
                'date': str(today),
                'is_market_open': market_status.is_market_open,
                'last_scraped': market_status.last_scraped,
                'total_turnover': float(market_status.total_turnover) if market_status.total_turnover else 0,
                'total_volume': market_status.total_volume,
                'total_transactions': market_status.total_transactions,
                'current_time': str(timezone.localtime()),
            })
        except MarketStatus.DoesNotExist:
            return Response({
                'status': 'success',
                'date': str(today),
                'is_market_open': False,
                'last_scraped': None,
                'message': 'No market data available for today',
                'current_time': str(timezone.localtime()),
            })

# scrapers/views.py - FIXED VERSION
class LatestStocksView(APIView):
    """Get latest stock data for today"""
    
    def get(self, request):
        try:
            # FIX: Use consistent Nepal timezone
            import pytz
            nepal_tz = pytz.timezone('Asia/Kathmandu')
            current_time = timezone.now().astimezone(nepal_tz)
            today = current_time.date()
            
            logger.info(f"[DEBUG] LatestStocksView called")
            logger.info(f"[DEBUG] UTC time: {timezone.now()}")
            logger.info(f"[DEBUG] Nepal time: {current_time}")
            logger.info(f"[DEBUG] Using date: {today}")
            
            # Get the latest scrape time for today
            latest_scrape = StockData.objects.filter(
                scrape_date=today
            ).aggregate(latest_time=Max('scrape_time'))['latest_time']
            
            logger.info(f"[DEBUG] Latest scrape time from DB: {latest_scrape}")
            
            if not latest_scrape:
                logger.warning(f"[DEBUG] No latest scrape time for {today}")
                # If no data for today, try to get the most recent data from any day
                latest_scrape_date = StockData.objects.aggregate(latest_date=Max('scrape_date'))['latest_date']
                logger.info(f"[DEBUG] Latest date in entire DB: {latest_scrape_date}")
                
                if latest_scrape_date:
                    latest_scrape = StockData.objects.filter(
                        scrape_date=latest_scrape_date
                    ).aggregate(latest_time=Max('scrape_time'))['latest_time']
                    
                    logger.info(f"[DEBUG] Fallback - Latest scrape time from {latest_scrape_date}: {latest_scrape}")
                    
                    # Get data from the latest available day
                    stocks = StockData.objects.filter(
                        scrape_date=latest_scrape_date,
                        scrape_time=latest_scrape
                    ).select_related('company').order_by('-percentage_change')
                    
                    logger.info(f"[DEBUG] Fallback - Queryset count: {stocks.count()}")
                    
                    serializer = StockDataSerializer(stocks, many=True)
                    
                    logger.info(f"[DEBUG] Fallback - Serialized count: {len(serializer.data)}")
                    
                    return Response({
                        'status': 'success',
                        'date': str(latest_scrape_date),
                        'scrape_time': latest_scrape,
                        'count': len(serializer.data),
                        'data': serializer.data,
                        'message': f'Showing latest available data from {latest_scrape_date}',
                        'debug': {
                            'today_requested': str(today),
                            'date_used': str(latest_scrape_date),
                            'reason': 'No data for today'
                        }
                    })
                else:
                    logger.warning("[DEBUG] No data found in entire database")
                    return Response({
                        'status': 'success',
                        'date': str(today),
                        'count': 0,
                        'data': [],
                        'message': 'No stock data available',
                        'debug': {
                            'today_requested': str(today),
                            'reason': 'Database empty'
                        }
                    })
            
            # Get latest data for today with company info
            stocks = StockData.objects.filter(
                scrape_date=today,
                scrape_time=latest_scrape
            ).select_related('company').order_by('-percentage_change')
            
            logger.info(f"[DEBUG] Main query - Queryset count: {stocks.count()}")
            
            if stocks.exists():
                logger.info(f"[DEBUG] First stock symbol: {stocks[0].symbol}")
                logger.info(f"[DEBUG] First stock company: {stocks[0].company.name if stocks[0].company else 'No company'}")
            
            serializer = StockDataSerializer(stocks, many=True)
            logger.info(f"[DEBUG] Main query - Serialized data count: {len(serializer.data)}")
            
            # Calculate summary statistics (UPDATED - no turnover)
            if stocks.exists():
                # Calculate average change
                changes = [float(stock.percentage_change) for stock in stocks if stock.percentage_change is not None]
                avg_change = sum(changes) / len(changes) if changes else 0
                
                # Find top gainer and loser
                stocks_with_change = [(stock, float(stock.percentage_change) if stock.percentage_change else 0) 
                                     for stock in stocks if stock.percentage_change is not None]
                
                if stocks_with_change:
                    top_gainer = max(stocks_with_change, key=lambda x: x[1])[0]
                    top_loser = min(stocks_with_change, key=lambda x: x[1])[0]
                    
                    summary = {
                        'average_percentage_change': round(avg_change, 2),
                        'top_gainer': {
                            'symbol': top_gainer.company.symbol if top_gainer.company else top_gainer.symbol,
                            'company_name': top_gainer.company.name if top_gainer.company else "Unknown",
                            'percentage_change': float(top_gainer.percentage_change) if top_gainer.percentage_change else 0,
                            'last_traded_price': float(top_gainer.last_traded_price) if top_gainer.last_traded_price else 0
                        },
                        'top_loser': {
                            'symbol': top_loser.company.symbol if top_loser.company else top_loser.symbol,
                            'company_name': top_loser.company.name if top_loser.company else "Unknown",
                            'percentage_change': float(top_loser.percentage_change) if top_loser.percentage_change else 0,
                            'last_traded_price': float(top_loser.last_traded_price) if top_loser.last_traded_price else 0
                        }
                    }
                else:
                    summary = {}
            else:
                summary = {}
            
            logger.info(f"[DEBUG] Returning response with {len(serializer.data)} records")
            
            return Response({
                'status': 'success',
                'date': str(today),
                'scrape_time': latest_scrape,
                'count': len(serializer.data),
                'summary': summary,
                'data': serializer.data,
                'debug': {
                    'today_used': str(today),
                    'scrape_time_used': str(latest_scrape),
                    'records_found': stocks.count(),
                    'records_serialized': len(serializer.data)
                }
            })
            
        except Exception as e:
            logger.error(f"[DEBUG] Error in LatestStocksView: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e),
                'debug': {
                    'error_type': type(e).__name__,
                    'traceback': str(e.__traceback__) if hasattr(e, '__traceback__') else 'No traceback'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TopGainersView(APIView):
    """Get top 10 gainers for today"""
    
    def get(self, request):
        try:
            today = timezone.now().date()
            
            # Get the latest scrape time for today
            latest_scrape = StockData.objects.filter(
                scrape_date=today
            ).aggregate(latest_time=Max('scrape_time'))['latest_time']
            
            if not latest_scrape:
                return Response({
                    'status': 'success',
                    'date': str(today),
                    'count': 0,
                    'data': [],
                    'message': 'No data available for today'
                })
            
            # Get top gainers with company info
            top_gainers = StockData.objects.filter(
                scrape_date=today,
                scrape_time=latest_scrape,
                percentage_change__gt=0
            ).select_related('company').order_by('-percentage_change')[:10]  # Already uses percentage_change
            
            serializer = StockDataSerializer(top_gainers, many=True)
            
            return Response({
                'status': 'success',
                'date': str(today),
                'scrape_time': latest_scrape,
                'count': len(serializer.data),
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error fetching top gainers: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TopLosersView(APIView):
    """Get top 10 losers for today"""
    
    def get(self, request):
        try:
            today = timezone.now().date()
            
            # Get the latest scrape time for today
            latest_scrape = StockData.objects.filter(
                scrape_date=today
            ).aggregate(latest_time=Max('scrape_time'))['latest_time']
            
            if not latest_scrape:
                return Response({
                    'status': 'success',
                    'date': str(today),
                    'count': 0,
                    'data': [],
                    'message': 'No data available for today'
                })
            
            # Get top losers with company info
            top_losers = StockData.objects.filter(
                scrape_date=today,
                scrape_time=latest_scrape,
                percentage_change__lt=0
            ).select_related('company').order_by('percentage_change')[:10]  # Already uses percentage_change
            
            serializer = StockDataSerializer(top_losers, many=True)
            
            return Response({
                'status': 'success',
                'date': str(today),
                'scrape_time': latest_scrape,
                'count': len(serializer.data),
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error fetching top losers: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

@csrf_exempt
def cron_simple_scrape(request):
    """Simple cron endpoint without authentication (for testing)"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Run scraping synchronously
        from .data_processor import NepseDataProcessor24x7
        processor = NepseDataProcessor24x7()
        result = processor.execute_24x7_scraping()
        
        logger.info(f"Cron scraping completed: {result}")
        return JsonResponse({
            'status': 'success',
            'records_saved': result.get('records_saved', 0),
            'message': result.get('message', ''),
            'timestamp': str(timezone.now()),
            'data': result
        })
    except Exception as e:
        logger.error(f"Cron scraping failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)
          
class CronTestView(APIView):
    """Test endpoint for cron job"""
    def get(self, request):
        return Response({
            'status': 'success',
            'message': 'Cron endpoint is working',
            'timestamp': timezone.now().isoformat(),
            'endpoint': '/api/cron/scrape/',
            'method': 'POST',
            'required_header': 'X-Cron-Secret',
            'note': 'Use POST method with X-Cron-Secret header for actual scraping'
        })
    
@csrf_exempt
def cron_simple(request):
    """Endpoint that actually scrapes and saves data"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Use GET method'}, status=405)
    
    logger.info(f"=== SCRAPING TRIGGERED via cron at {timezone.now()} ===")
    
    try:
        # THIS IS WHAT SCRAPES DATA
        from .data_processor import NepseDataProcessor24x7
        processor = NepseDataProcessor24x7()
        
        # This function does the actual scraping and saving
        result = processor.execute_24x7_scraping()
        
        # Check if data was saved
        records_saved = result.get('records_saved', 0)
        
        if records_saved > 0:
            message = f"✅ Successfully scraped and saved {records_saved} stock records"
        else:
            message = "⚠️ Scraping completed but no new records saved"
        
        logger.info(f"Scraping result: {result}")
        
        return JsonResponse({
            'status': 'success',
            'message': message,
            'records_saved': records_saved,
            'data_source': result.get('data_source_used', 'unknown'),
            'market_session': result.get('market_session', 'unknown'),
            'timestamp': str(timezone.now())
        })
        
    except Exception as e:
        logger.error(f"❌ Scraping failed: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': str(timezone.now())
        }, status=500)