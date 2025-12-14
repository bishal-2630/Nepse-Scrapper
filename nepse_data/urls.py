from django.urls import path
from .api_views import StockDataView, LatestStockDataView
from .top_views import TopGainersView, TopLosersView

app_name = 'nepse_data'

urlpatterns = [
    # Stock Prices
    path('api/stocks/', StockDataView.as_view(), name='stock-data'),
    path('api/stocks/latest/', LatestStockDataView.as_view(), name='latest-stocks'),
    
    # Top Performers
    path('api/top-gainers/', TopGainersView.as_view(), name='top-gainers'),
    path('api/top-losers/', TopLosersView.as_view(), name='top-losers'),
]