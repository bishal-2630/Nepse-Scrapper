# nepse_data/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Max, Min, Q
from datetime import datetime
import json
import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from .models import DailyStockData, Company, TopGainers, TopLosers
from .scrapers import NepseScraper
from .serializers import StockDataSerializer, CompanySerializer, TopGainersSerializer, TopLosersSerializer

logger = logging.getLogger(__name__)

# ==================== DRF API Views (Data Access Only) ====================

class LatestStocksAPI(APIView):
    """Get latest stock data"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get today's date
        today = timezone.now().date()
        
        # Check if we have today's data
        today_exists = DailyStockData.objects.filter(date=today).exists()
        
        if today_exists:
            # Return today's data
            stocks = DailyStockData.objects.filter(date=today)\
                       .select_related('company')\
                       .order_by('company__symbol')
            latest_date = today
        else:
            # Return most recent available date's data
            latest_date_result = DailyStockData.objects.aggregate(latest_date=Max('date'))
            latest_date = latest_date_result.get('latest_date')
            
            if not latest_date:
                return Response({
                    'status': 'success',
                    'message': 'No stock data available',
                    'data_date': None,
                    'total_stocks': 0,
                    'data': [],
                    'market_summary': {
                        'gainers': 0,
                        'losers': 0,
                        'unchanged': 0,
                        'total_volume': 0,
                        'average_change': 0,
                        'market_sentiment': 'neutral'
                    },
                    'is_today_data': False
                })
            
            stocks = DailyStockData.objects.filter(date=latest_date)\
                       .select_related('company')\
                       .order_by('company__symbol')
        
        # Serialize the data
        serializer = StockDataSerializer(stocks, many=True)
        
        # Calculate market summary
        total_count = stocks.count()
        if total_count > 0:
            gainers_count = stocks.filter(change_percent__gt=0).count()
            losers_count = stocks.filter(change_percent__lt=0).count()
            unchanged_count = stocks.filter(change_percent=0).count()
            
            try:
                total_volume = sum(stock.volume for stock in stocks if stock.volume)
                avg_change = sum(float(stock.change_percent) for stock in stocks if stock.change_percent) / total_count
            except:
                total_volume = 0
                avg_change = 0
        else:
            gainers_count = losers_count = unchanged_count = total_volume = avg_change = 0
        
        market_summary = {
            'gainers': gainers_count,
            'losers': losers_count,
            'unchanged': unchanged_count,
            'total_stocks': total_count,
            'total_volume': total_volume,
            'average_change': round(avg_change, 2),
            'market_sentiment': 'bullish' if avg_change > 0 else 'bearish' if avg_change < 0 else 'neutral'
        }
        
        return Response({
            'status': 'success',
            'message': f'Found {total_count} stocks',
            'data_date': latest_date.isoformat() if latest_date else None,
            'total_stocks': total_count,
            'data': serializer.data,
            'market_summary': market_summary,
            'is_today_data': today_exists,
            'next_scrape_scheduled': 'Mon-Fri at 11:30 AM, 12:00 PM, 1:30 PM Nepal Time'
        })

class TopGainersAPI(APIView):
    """Get top gainers"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get the latest date
        latest_date_result = DailyStockData.objects.aggregate(latest_date=Max('date'))
        latest_date = latest_date_result.get('latest_date')
        
        if not latest_date:
            return Response({
                'status': 'success',
                'message': 'No data available',
                'data_date': None,
                'gainers': []
            })
        
        # Try to get from TopGainers table first
        gainers_from_table = TopGainers.objects.filter(date=latest_date)\
                              .select_related('company')\
                              .order_by('rank')
        
        if gainers_from_table.exists():
            serializer = TopGainersSerializer(gainers_from_table, many=True)
            gainers = serializer.data
        else:
            # Calculate from DailyStockData
            daily_data = DailyStockData.objects.filter(date=latest_date)\
                          .select_related('company')\
                          .filter(change_percent__gt=0)\
                          .order_by('-change_percent')[:10]
            
            gainers = []
            for i, data in enumerate(daily_data, 1):
                gainers.append({
                    'rank': i,
                    'symbol': data.company.symbol,
                    'company_name': data.company.name,
                    'sector': data.company.sector or 'N/A',
                    'change_percent': float(data.change_percent),
                    'close_price': float(data.close_price),
                    'volume': data.volume
                })
        
        return Response({
            'status': 'success',
            'data_date': latest_date.isoformat(),
            'is_today_data': latest_date == timezone.now().date(),
            'gainers': gainers,
            'count': len(gainers)
        })

class TopLosersAPI(APIView):
    """Get top losers"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get the latest date
        latest_date_result = DailyStockData.objects.aggregate(latest_date=Max('date'))
        latest_date = latest_date_result.get('latest_date')
        
        if not latest_date:
            return Response({
                'status': 'success',
                'message': 'No data available',
                'data_date': None,
                'losers': []
            })
        
        # Try to get from TopLosers table first
        losers_from_table = TopLosers.objects.filter(date=latest_date)\
                             .select_related('company')\
                             .order_by('rank')
        
        if losers_from_table.exists():
            serializer = TopLosersSerializer(losers_from_table, many=True)
            losers = serializer.data
        else:
            # Calculate from DailyStockData
            daily_data = DailyStockData.objects.filter(date=latest_date)\
                          .select_related('company')\
                          .filter(change_percent__lt=0)\
                          .order_by('change_percent')[:10]
            
            losers = []
            for i, data in enumerate(daily_data, 1):
                losers.append({
                    'rank': i,
                    'symbol': data.company.symbol,
                    'company_name': data.company.name,
                    'sector': data.company.sector or 'N/A',
                    'change_percent': float(data.change_percent),
                    'close_price': float(data.close_price),
                    'volume': data.volume
                })
        
        return Response({
            'status': 'success',
            'data_date': latest_date.isoformat(),
            'is_today_data': latest_date == timezone.now().date(),
            'losers': losers,
            'count': len(losers)
        })

@api_view(['GET'])
@permission_classes([AllowAny])
def system_status_api(request):
    """Get system status and data statistics"""
    try:
        from .models import DailyStockData
        from django.utils import timezone
        from datetime import datetime
        import pytz
        
        today = timezone.now().date()
        nepal_tz = pytz.timezone('Asia/Kathmandu')
        current_nepal_time = datetime.now(nepal_tz)
        
        # Check today's data
        today_count = DailyStockData.objects.filter(date=today).count()
        today_exists = today_count > 0
        
        # Get latest date in database
        latest_date_result = DailyStockData.objects.aggregate(latest_date=Max('date'))
        latest_date = latest_date_result.get('latest_date')
        
        # Check if market is open
        weekday = current_nepal_time.weekday()
        hour = current_nepal_time.hour
        is_market_day = weekday < 5  # Monday-Friday
        is_market_hours = 11 <= hour < 15
        
        market_status = "closed"
        if is_market_day and is_market_hours:
            market_status = "open"
        elif not is_market_day:
            market_status = "weekend"
        
        return Response({
            'status': 'success',
            'current': {
                'date': today.isoformat(),
                'nepal_time': current_nepal_time.strftime('%Y-%m-%d %H:%M:%S'),
                'day': current_nepal_time.strftime('%A'),
                'market_status': market_status,
                'has_today_data': today_exists,
                'today_records': today_count
            },
            'database': {
                'total_companies': Company.objects.count(),
                'total_records': DailyStockData.objects.count(),
                'earliest_date': DailyStockData.objects.aggregate(earliest=Min('date'))['earliest'],
                'latest_date': latest_date,
                'latest_date_records': DailyStockData.objects.filter(date=latest_date).count() if latest_date else 0,
            },
            'automation': {
                'scraping_enabled': True,
                'schedule': 'Every 30 minutes',
                'market_hours_only': True,
                'next_check': 'Within 30 minutes'
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return Response({
            'status': 'error',
            'message': f'Error getting status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==================== Django Function Views (Legacy - Data Access Only) ====================

def get_latest_stocks(request):
    """Get latest stock data (legacy)"""
    view = LatestStocksAPI()
    return view.get(request._request if hasattr(request, '_request') else request)

def get_top_gainers(request):
    """Get top gainers (legacy)"""
    view = TopGainersAPI()
    return view.get(request._request if hasattr(request, '_request') else request)

def get_top_losers(request):
    """Get top losers (legacy)"""
    view = TopLosersAPI()
    return view.get(request._request if hasattr(request, '_request') else request)

def system_status(request):
    """Get system status (legacy)"""
    return system_status_api(request._request if hasattr(request, '_request') else request)

# ==================== Additional Function Views ====================

def get_stocks_by_date(request, date_str=None):
    """Get stock data for a specific date"""
    try:
        # If no date provided, use query parameter or today
        if not date_str:
            date_str = request.GET.get('date')
            if not date_str:
                target_date = timezone.now().date()
            else:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            # Parse date string (YYYY-MM-DD)
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get data for the specified date
        stocks = DailyStockData.objects.filter(date=target_date)\
                   .select_related('company')\
                   .order_by('company__symbol')
        
        if not stocks.exists():
            # Try to find nearest available date
            nearest_date = DailyStockData.objects.filter(date__lt=target_date)\
                              .order_by('-date')\
                              .values('date')\
                              .first()
            
            if nearest_date:
                target_date = nearest_date['date']
                stocks = DailyStockData.objects.filter(date=target_date)\
                           .select_related('company')\
                           .order_by('company__symbol')
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f'No data available for {target_date} or any previous date'
                }, status=404)
        
        # Format the data
        data = []
        for stock in stocks:
            stock_data = {
                'symbol': stock.company.symbol,
                'company_name': stock.company.name,
                'sector': stock.company.sector or 'N/A',
                'date': stock.date.isoformat(),
                'open': float(stock.open_price) if stock.open_price is not None else None,
                'high': float(stock.high_price) if stock.high_price is not None else None,
                'low': float(stock.low_price) if stock.low_price is not None else None,
                'close': float(stock.close_price) if stock.close_price is not None else None,
                'volume': stock.volume,
                'change': float(stock.change) if stock.change is not None else None,
                'change_percent': float(stock.change_percent) if stock.change_percent is not None else None,
            }
            data.append(stock_data)
        
        # Count gainers and losers
        gainers = stocks.filter(change_percent__gt=0).count()
        losers = stocks.filter(change_percent__lt=0).count()
        
        return JsonResponse({
            'status': 'success',
            'date': target_date.isoformat(),
            'total_stocks': len(data),
            'gainers': gainers,
            'losers': losers,
            'data': data
        })
        
    except ValueError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid date format. Use YYYY-MM-DD'
        }, status=400)
    except Exception as e:
        logger.error(f"Error fetching stocks by date: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error fetching data: {str(e)}'
        }, status=500)

def get_stock_history(request, symbol):
    """Get historical data for a specific stock"""
    try:
        # Get the company
        company = Company.objects.get(symbol=symbol.upper())
        
        # Get historical data (last 30 days by default)
        days = request.GET.get('days', 30)
        try:
            days = int(days)
            if days > 365:  # Limit to 1 year
                days = 365
        except:
            days = 30
        
        # Calculate date range
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=days)
        
        # Get data
        history = DailyStockData.objects.filter(
            company=company,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # Format response
        data = []
        for record in history:
            data.append({
                'date': record.date.isoformat(),
                'open': float(record.open_price) if record.open_price is not None else None,
                'high': float(record.high_price) if record.high_price is not None else None,
                'low': float(record.low_price) if record.low_price is not None else None,
                'close': float(record.close_price) if record.close_price is not None else None,
                'volume': record.volume,
                'change': float(record.change) if record.change is not None else None,
                'change_percent': float(record.change_percent) if record.change_percent is not None else None,
            })
        
        return JsonResponse({
            'status': 'success',
            'symbol': company.symbol,
            'company_name': company.name,
            'sector': company.sector,
            'period': f'{start_date} to {end_date}',
            'days': days,
            'data_points': len(data),
            'data': data
        })
        
    except Company.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': f'Stock symbol "{symbol}" not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error fetching stock history for {symbol}: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error fetching data: {str(e)}'
        }, status=500)

def search_stocks(request):
    """Search stocks by symbol or company name"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({
            'status': 'error',
            'message': 'Search query must be at least 2 characters'
        }, status=400)
    
    try:
        # Search in companies
        companies = Company.objects.filter(
            Q(symbol__icontains=query) | 
            Q(name__icontains=query)
        )[:20]  # Limit results
        
        # Get latest data for these companies
        latest_date_result = DailyStockData.objects.aggregate(latest_date=Max('date'))
        latest_date = latest_date_result.get('latest_date')
        
        results = []
        for company in companies:
            # Try to get latest stock data
            latest_data = DailyStockData.objects.filter(
                company=company,
                date=latest_date
            ).first()
            
            result = {
                'symbol': company.symbol,
                'company_name': company.name,
                'sector': company.sector or 'N/A',
            }
            
            if latest_data:
                result.update({
                    'date': latest_date.isoformat(),
                    'close_price': float(latest_data.close_price) if latest_data.close_price else None,
                    'change_percent': float(latest_data.change_percent) if latest_data.change_percent else None,
                    'volume': latest_data.volume,
                    'has_data': True
                })
            else:
                result['has_data'] = False
            
            results.append(result)
        
        return JsonResponse({
            'status': 'success',
            'query': query,
            'results': results,
            'count': len(results),
            'data_date': latest_date.isoformat() if latest_date else None
        })
        
    except Exception as e:
        logger.error(f"Error searching stocks: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Search error: {str(e)}'
        }, status=500)