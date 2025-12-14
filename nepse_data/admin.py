from django.contrib import admin
from .models import Company, DailyStockData, IndexData, TopGainers, TopLosers

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'sector')
    search_fields = ('symbol', 'name')
    list_filter = ('sector',)

@admin.register(DailyStockData)
class DailyStockDataAdmin(admin.ModelAdmin):
    list_display = ('company', 'date', 'close_price', 'volume', 'change_percent')
    list_filter = ('date', 'company__sector')
    search_fields = ('company__symbol', 'company__name')
    date_hierarchy = 'date'

@admin.register(IndexData)
class IndexDataAdmin(admin.ModelAdmin):
    list_display = ('index_name', 'date', 'current_value', 'change_percent')
    list_filter = ('index_name', 'date')
    date_hierarchy = 'date'

@admin.register(TopGainers)
class TopGainersAdmin(admin.ModelAdmin):
    list_display = ('date', 'rank', 'company', 'change_percent', 'close_price')
    list_filter = ('date', 'company__sector')
    ordering = ('-date', 'rank')
    date_hierarchy = 'date'

@admin.register(TopLosers)
class TopLosersAdmin(admin.ModelAdmin):
    list_display = ('date', 'rank', 'company', 'change_percent', 'close_price')
    list_filter = ('date', 'company__sector')
    ordering = ('-date', 'rank')
    date_hierarchy = 'date'