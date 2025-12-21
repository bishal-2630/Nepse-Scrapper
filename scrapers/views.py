# scrapers/views.py - UPDATED VERSION
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Max, Q, Avg
from .models import StockData, MarketStatus, Company
from .serializers import StockDataSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import pytz
import logging

logger = logging.getLogger(__name__)

class MarketStatusView(APIView):
    """Get current market status"""
    
    def get(self, request):
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
    """Get latest stock data for ALL symbols"""
    
    def get(self, request):
        try:
            # Get the LATEST date in the database
            latest_date_result = StockData.objects.aggregate(latest_date=Max('scrape_date'))
            latest_date = latest_date_result.get('latest_date')
            
            if not latest_date:
                return Response({
                    'status': 'success',
                    'date': None,
                    'count': 0,
                    'data': [],
                    'message': 'No stock data available in database',
                    'timestamp': str(timezone.now())
                })
            
            # Get the latest scrape time for that date
            latest_time_result = StockData.objects.filter(
                scrape_date=latest_date
            ).aggregate(latest_time=Max('scrape_time'))
            latest_time = latest_time_result.get('latest_time')
            
            if not latest_time:
                return Response({
                    'status': 'success',
                    'date': str(latest_date),
                    'count': 0,
                    'data': [],
                    'message': 'No data found for the latest date',
                    'timestamp': str(timezone.now())
                })
            
            # Get all data for the latest date/time
            stocks = StockData.objects.filter(
                scrape_date=latest_date,
                scrape_time=latest_time
            ).select_related('company').order_by('-percentage_change')
            
            serializer = StockDataSerializer(stocks, many=True)
            
            # Calculate summary statistics
            summary = self._calculate_summary(stocks)
            
            return Response({
                'status': 'success',
                'date': str(latest_date),
                'scrape_time': str(latest_time),
                'count': len(serializer.data),
                'summary': summary,
                'data': serializer.data,
                'timestamp': str(timezone.now())
            })
            
        except Exception as e:
            logger.error(f"Error in LatestStocksView: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _calculate_summary(self, queryset):
        """Calculate summary statistics for the given queryset"""
        if not queryset.exists():
            return {}
        
        # Calculate average percentage change
        avg_result = queryset.filter(
            percentage_change__isnull=False
        ).aggregate(avg_change=Avg('percentage_change'))
        
        avg_change = avg_result.get('avg_change')
        
        # Find top gainer and loser
        top_gainer = queryset.filter(
            percentage_change__isnull=False
        ).order_by('-percentage_change').first()
        
        top_loser = queryset.filter(
            percentage_change__isnull=False
        ).order_by('percentage_change').first()
        
        summary = {}
        
        if avg_change is not None:
            summary['average_percentage_change'] = float(avg_change)
        
        if top_gainer:
            summary['top_gainer'] = {
                'symbol': top_gainer.symbol,
                'company_name': top_gainer.company.name if top_gainer.company else top_gainer.symbol,
                'percentage_change': float(top_gainer.percentage_change) if top_gainer.percentage_change else 0,
                'last_traded_price': float(top_gainer.last_traded_price) if top_gainer.last_traded_price else 0
            }
        
        if top_loser:
            summary['top_loser'] = {
                'symbol': top_loser.symbol,
                'company_name': top_loser.company.name if top_loser.company else top_loser.symbol,
                'percentage_change': float(top_loser.percentage_change) if top_loser.percentage_change else 0,
                'last_traded_price': float(top_loser.last_traded_price) if top_loser.last_traded_price else 0
            }
        
        summary['total_companies'] = queryset.count()
        
        return summary

class TopGainersView(APIView):
    """Get top 10 gainers"""
    
    def get(self, request):
        try:
            # Get the LATEST date in the database
            latest_date_result = StockData.objects.aggregate(latest_date=Max('scrape_date'))
            latest_date = latest_date_result.get('latest_date')
            
            if not latest_date:
                return Response({
                    'status': 'success',
                    'date': None,
                    'count': 0,
                    'data': [],
                    'message': 'No data available'
                })
            
            # Get the latest scrape time for that date
            latest_time_result = StockData.objects.filter(
                scrape_date=latest_date
            ).aggregate(latest_time=Max('scrape_time'))
            latest_time = latest_time_result.get('latest_time')
            
            if not latest_time:
                return Response({
                    'status': 'success',
                    'date': str(latest_date),
                    'count': 0,
                    'data': [],
                    'message': 'No data found for the latest date'
                })
            
            # Get top gainers (positive change)
            top_gainers = StockData.objects.filter(
                scrape_date=latest_date,
                scrape_time=latest_time,
                percentage_change__gt=0
            ).select_related('company').order_by('-percentage_change')[:10]
            
            serializer = StockDataSerializer(top_gainers, many=True)
            
            return Response({
                'status': 'success',
                'date': str(latest_date),
                'scrape_time': str(latest_time),
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
    """Get top 10 losers"""
    
    def get(self, request):
        try:
            # Get the LATEST date in the database
            latest_date_result = StockData.objects.aggregate(latest_date=Max('scrape_date'))
            latest_date = latest_date_result.get('latest_date')
            
            if not latest_date:
                return Response({
                    'status': 'success',
                    'date': None,
                    'count': 0,
                    'data': [],
                    'message': 'No data available'
                })
            
            # Get the latest scrape time for that date
            latest_time_result = StockData.objects.filter(
                scrape_date=latest_date
            ).aggregate(latest_time=Max('scrape_time'))
            latest_time = latest_time_result.get('latest_time')
            
            if not latest_time:
                return Response({
                    'status': 'success',
                    'date': str(latest_date),
                    'count': 0,
                    'data': [],
                    'message': 'No data found for the latest date'
                })
            
            # Get top losers (negative change)
            top_losers = StockData.objects.filter(
                scrape_date=latest_date,
                scrape_time=latest_time,
                percentage_change__lt=0
            ).select_related('company').order_by('percentage_change')[:10]
            
            serializer = StockDataSerializer(top_losers, many=True)
            
            return Response({
                'status': 'success',
                'date': str(latest_date),
                'scrape_time': str(latest_time),
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
        
        # Run scraping
        result = processor.execute_24x7_scraping()
        
        # Log detailed result
        logger.info(f"Forced scraping result: {result}")
        
        return JsonResponse({
            'status': 'success',
            'companies_updated': result.get('companies_updated', '0 created, 0 updated'),
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