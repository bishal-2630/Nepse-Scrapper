from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import DailyStockData
from datetime import datetime

class TopGainersView(APIView):
    """
    Get top gaining stocks.
    """
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                description="Number of top gainers (default: 10)",
                type=openapi.TYPE_INTEGER,
                default=10
            ),
        ],
        responses={
            200: openapi.Response(
                description="Top gainers data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'top_gainers': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'rank': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'symbol': openapi.Schema(type=openapi.TYPE_STRING),
                                    'company_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'change_percent': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                                    'close_price': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                                }
                            )
                        )
                    }
                )
            ),
        },
        operation_description="Get today's top gaining stocks"
    )
    def get(self, request):
        """Get top gaining stocks"""
      
        try:
            latest_data = DailyStockData.objects.latest('date')
            target_date = latest_data.date
        except DailyStockData.DoesNotExist:
            return Response(
                {"error": "No stock data available"},
                status=status.HTTP_404_NOT_FOUND
            )
        
     
        try:
            limit = min(int(request.GET.get('limit', 10)), 20)
        except ValueError:
            limit = 10
        
      
        daily_data = DailyStockData.objects.filter(date=target_date, change_percent__isnull=False)
        
        if not daily_data.exists():
            return Response(
                {"error": f"No data available for {target_date}"},
                status=status.HTTP_404_NOT_FOUND
            )
        
     
        gainers = daily_data.filter(change_percent__gt=0).order_by('-change_percent')[:limit]
        
       
        top_gainers = []
        for i, data in enumerate(gainers, 1):
            top_gainers.append({
                'rank': i,
                'symbol': data.company.symbol,
                'company_name': data.company.name,
                'change_percent': float(data.change_percent) if data.change_percent else 0,
                'close_price': float(data.close_price) if data.close_price else 0,
            })
        
        return Response({
            'date': target_date,
            'count': len(top_gainers),
            'top_gainers': top_gainers
        })

class TopLosersView(APIView):
    """
    Get top losing stocks.
    """
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                description="Number of top losers (default: 10)",
                type=openapi.TYPE_INTEGER,
                default=10
            ),
        ],
        responses={
            200: openapi.Response(
                description="Top losers data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'top_losers': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'rank': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'symbol': openapi.Schema(type=openapi.TYPE_STRING),
                                    'company_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'change_percent': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                                    'close_price': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                                }
                            )
                        )
                    }
                )
            ),
        },
        operation_description="Get today's top losing stocks"
    )
    def get(self, request):
        """Get top losing stocks"""
        # Get latest available date
        try:
            latest_data = DailyStockData.objects.latest('date')
            target_date = latest_data.date
        except DailyStockData.DoesNotExist:
            return Response(
                {"error": "No stock data available"},
                status=status.HTTP_404_NOT_FOUND
            )
        
       
        try:
            limit = min(int(request.GET.get('limit', 10)), 20)
        except ValueError:
            limit = 10
        
       
        daily_data = DailyStockData.objects.filter(date=target_date, change_percent__isnull=False)
        
        if not daily_data.exists():
            return Response(
                {"error": f"No data available for {target_date}"},
                status=status.HTTP_404_NOT_FOUND
            )
        
     
        losers = daily_data.filter(change_percent__lt=0).order_by('change_percent')[:limit]
        
       
        top_losers = []
        for i, data in enumerate(losers, 1):
            top_losers.append({
                'rank': i,
                'symbol': data.company.symbol,
                'company_name': data.company.name,
                'change_percent': float(data.change_percent) if data.change_percent else 0,
                'close_price': float(data.close_price) if data.close_price else 0,
            })
        
        return Response({
            'date': target_date,
            'count': len(top_losers),
            'top_losers': top_losers
        })