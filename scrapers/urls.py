# scrapers/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('status/', views.MarketStatusView.as_view(), name='market-status'),
    path('stocks/latest/', views.LatestStocksView.as_view(), name='latest-stocks'),
    path('stocks/top-gainers/', views.TopGainersView.as_view(), name='top-gainers'),
    path('stocks/top-losers/', views.TopLosersView.as_view(), name='top-losers'),
    path('cron/test/', views.CronTestView.as_view(), name='cron-test'), 
    path('cron/simple/', views.cron_simple_scrape, name='cron-simple'),
]