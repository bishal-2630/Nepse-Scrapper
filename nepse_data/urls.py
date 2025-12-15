# nepse_data/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # API Endpoints (for Swagger documentation)
    path('api/scrape/', views.scrape_now_api, name='api-scrape'),
    path('api/scrape-fresh/', views.scrape_fresh_today_api, name='api-scrape-fresh'),
    path('api/stocks/latest/', views.LatestStocksAPI.as_view(), name='api-latest-stocks'),
    path('api/top-gainers/', views.TopGainersAPI.as_view(), name='api-top-gainers'),
    path('api/top-losers/', views.TopLosersAPI.as_view(), name='api-top-losers'),
    path('api/status/', views.system_status_api, name='api-system-status'),
    
    # Legacy endpoints (keep for backward compatibility)
    path('scrape/', views.scrape_now, name='scrape'),
    path('scrape-fresh/', views.scrape_fresh_today, name='scrape-fresh'),
    path('stocks/latest/', views.get_latest_stocks, name='latest-stocks'),
    path('top-gainers/', views.get_top_gainers, name='top-gainers'),
    path('top-losers/', views.get_top_losers, name='top-losers'),
    path('status/', views.system_status, name='system-status'),
    
    # Other endpoints (these won't appear in Swagger unless you convert them too)
    path('stocks/date/', views.get_stocks_by_date, name='stocks-by-date'),
    path('stocks/date/<str:date_str>/', views.get_stocks_by_date, name='stocks-by-date-specific'),
    path('stocks/<str:symbol>/history/', views.get_stock_history, name='stock-history'),
    path('stocks/search/', views.search_stocks, name='search-stocks'),
]