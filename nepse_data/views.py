from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import DailyStockData
from .scrapers import NepseScraper
import json

@csrf_exempt
def scrape_now(request):
    """Manual trigger for scraping"""
    if request.method == 'POST':
        try:
            # Scrape data
            stock_data = NepseScraper.scrape_today_prices()
            
            if stock_data:
                # Save to database
                saved_count = NepseScraper.save_to_database(stock_data)
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Scraped {len(stock_data)} stocks, saved {saved_count} records',
                    'data_count': len(stock_data),
                    'saved_count': saved_count
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No data scraped. The website structure might have changed.'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Scraping failed: {str(e)}'
            })
    
    return JsonResponse({'message': 'Send POST request to scrape data'})

class StockListView(View):
    def get(self, request):
        """List all stock data"""
        stocks = DailyStockData.objects.all().order_by('-date')[:50]
        
        data = []
        for stock in stocks:
            data.append({
                'symbol': stock.company.symbol,
                'company': stock.company.name,
                'date': stock.date.strftime('%Y-%m-%d'),
                'open': float(stock.open_price) if stock.open_price else None,
                'high': float(stock.high_price) if stock.high_price else None,
                'low': float(stock.low_price) if stock.low_price else None,
                'close': float(stock.close_price) if stock.close_price else None,
                'volume': stock.volume,
                'change': float(stock.change) if stock.change else None,
                'change_percent': float(stock.change_percent) if stock.change_percent else None,
            })
        
        return JsonResponse({
            'status': 'success',
            'count': len(data),
            'data': data
        })