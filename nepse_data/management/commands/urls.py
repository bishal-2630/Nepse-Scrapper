from django.urls import path
from . import views

urlpatterns = [
    path('api/stocks/', views.StockDataView.as_view(), name='stock-data'),
    path('api/stocks/latest/', views.LatestStockDataView.as_view(), name='latest-stocks'),
    path('api/indices/', views.IndexDataView.as_view(), name='index-data'),
]