# scrapers/admin.py - UPDATED
from django.contrib import admin
from .models import Company, StockData, MarketStatus

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'sector', 'is_active', 'created_at')
    search_fields = ('symbol', 'name')
    list_filter = ('sector', 'is_active')

@admin.register(StockData)
class StockDataAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'close_price', 'percentage_change', 'scrape_date', 'scrape_time', 'data_source')
    list_filter = ('scrape_date', 'data_source', 'is_closing_data')
    search_fields = ('symbol', 'company__name')
    readonly_fields = ('created_at',)
    
    def symbol(self, obj):
        return obj.symbol
    symbol.short_description = 'Symbol'
    symbol.admin_order_field = 'symbol'

@admin.register(MarketStatus)
class MarketStatusAdmin(admin.ModelAdmin):
    list_display = ('date', 'is_market_open', 'total_turnover', 'last_scraped')
    list_filter = ('is_market_open', 'date')
    readonly_fields = ('created_at', 'updated_at')