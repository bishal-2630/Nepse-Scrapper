from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import DailyStockData
from .serializers import StockDataSerializer
from django.core.paginator import Paginator

class StockDataView(APIView):
    """
    Get stock data with filtering options.
    """
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'symbol',
                openapi.IN_QUERY,
                description="Filter by company symbol",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'start_date',
                openapi.IN_QUERY,
                description="Start date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'end_date',
                openapi.IN_QUERY,
                description="End date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
                default=1
            ),
        ],
        responses={
            200: openapi.Response('Stock data', StockDataSerializer(many=True)),
        },
        operation_description="Get stock price data with optional filtering"
    )
    def get(self, request):
        """Get stock price data"""
        queryset = DailyStockData.objects.all().order_by('-date')
        
        # Filter by symbol
        symbol = request.GET.get('symbol')
        if symbol:
            queryset = queryset.filter(company__symbol__iexact=symbol)
        
        # Filter by date range
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        paginator = Paginator(queryset, 50)
        
        try:
            stocks_page = paginator.page(page)
        except:
            return Response(
                {"error": "Invalid page number"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = StockDataSerializer(stocks_page, many=True)
        
        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'results': serializer.data
        })

class LatestStockDataView(APIView):
    """
    Get the latest stock prices for all companies.
    """
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response('Latest stock prices', StockDataSerializer(many=True)),
        },
        operation_description="Get today's latest stock prices"
    )
    def get(self, request):
        """Get latest stock prices"""
        try:
            latest_date = DailyStockData.objects.latest('date').date
            stocks = DailyStockData.objects.filter(date=latest_date).order_by('company__symbol')
            
            serializer = StockDataSerializer(stocks, many=True)
            
            return Response({
                'date': latest_date,
                'count': stocks.count(),
                'results': serializer.data
            })
        except DailyStockData.DoesNotExist:
            return Response({
                'date': None,
                'count': 0,
                'results': []
            }, status=status.HTTP_404_NOT_FOUND)