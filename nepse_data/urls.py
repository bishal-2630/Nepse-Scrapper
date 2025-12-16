# nepse_data/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # API Endpoints (Data Access Only - No Manual Scraping)
    path('api/stocks/latest/', views.LatestStocksAPI.as_view(), name='api-latest-stocks'),
    path('api/top-gainers/', views.TopGainersAPI.as_view(), name='api-top-gainers'),
    path('api/top-losers/', views.TopLosersAPI.as_view(), name='api-top-losers'),
    path('api/status/', views.system_status_api, name='api-system-status'),
    
    # Legacy endpoints (Data Access Only)
    path('stocks/latest/', views.get_latest_stocks, name='latest-stocks'),
    path('top-gainers/', views.get_top_gainers, name='top-gainers'),
    path('top-losers/', views.get_top_losers, name='top-losers'),
    path('status/', views.system_status, name='system-status'),
    
    # Data query endpoints
    path('stocks/date/', views.get_stocks_by_date, name='stocks-by-date'),
    path('stocks/date/<str:date_str>/', views.get_stocks_by_date, name='stocks-by-date-specific'),
    path('stocks/<str:symbol>/history/', views.get_stock_history, name='stock-history'),
    path('stocks/search/', views.search_stocks, name='search-stocks'),
]