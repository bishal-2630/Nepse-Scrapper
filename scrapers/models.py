# scrapers/models.py
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class Company(models.Model):
    """Company information - ID is primary key, symbol is unique"""
    symbol = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100, blank=True, null=True)
    listed_shares = models.BigIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['symbol']
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['sector']),
        ]
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"

class StockData(models.Model):
    """Daily stock price data - ONLY fields available from unofficial API"""
    DATA_SOURCE_CHOICES = [
        ('live', 'Live Market'),
        ('closing', 'Closing Summary'),
        ('historical', 'Historical'),
    ]
    
    # Relationships
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_data')
    symbol = models.CharField(max_length=20, db_index=True)
    
    # ✅ ACTUAL DATA WE CAN GET FROM UNOFFICIAL API
    close_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_traded_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    previous_close = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    difference = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    percentage_change = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Metadata
    scrape_date = models.DateField(db_index=True)
    scrape_time = models.TimeField(db_index=True)
    data_source = models.CharField(max_length=20, choices=DATA_SOURCE_CHOICES, default='live')
    is_closing_data = models.BooleanField(default=False, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Stock Data"
        indexes = [
            models.Index(fields=['scrape_date', 'symbol']),
            models.Index(fields=['symbol', 'scrape_date']),
            models.Index(fields=['scrape_date', 'percentage_change']),
            models.Index(fields=['scrape_date', 'data_source']),
            models.Index(fields=['is_closing_data']),
        ]
        unique_together = ['company', 'scrape_date', 'scrape_time', 'data_source']
        ordering = ['-scrape_date', '-scrape_time', 'symbol']
    
    def save(self, *args, **kwargs):
        """Auto-populate symbol from company before saving"""
        if self.company and not self.symbol:
            self.symbol = self.company.symbol
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.symbol} - {self.scrape_date} {self.scrape_time}"

class MarketStatus(models.Model):
    """Daily market status"""
    date = models.DateField(unique=True)
    is_market_open = models.BooleanField(default=False)
    last_scraped = models.DateTimeField(null=True, blank=True)
    total_turnover = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_volume = models.BigIntegerField(default=0)
    total_transactions = models.IntegerField(default=0)
    market_close_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Market Status"
        ordering = ['-date']
    
    def __str__(self):
        return f"Market {self.date}: {'OPEN' if self.is_market_open else 'CLOSED'}"