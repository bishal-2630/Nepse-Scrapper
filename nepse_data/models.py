from django.db import models
from django.utils import timezone

class Company(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100, blank=True, null=True)
    instrument_type = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"

class DailyStockData(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='daily_data')
    date = models.DateField()
    open_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    high_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    low_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    close_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    change = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    change_percent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['company', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.company.symbol} - {self.date}"

class IndexData(models.Model):
    index_name = models.CharField(max_length=100)
    date = models.DateField()
    current_value = models.DecimalField(max_digits=10, decimal_places=2)
    change = models.DecimalField(max_digits=10, decimal_places=2)
    change_percent = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ['index_name', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.index_name} - {self.date}"

class TopGainers(models.Model):
    date = models.DateField()
    rank = models.IntegerField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    change_percent = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField(null=True, blank=True)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ['date', 'rank', 'company']
        ordering = ['-date', 'rank']
    
    def __str__(self):
        return f"Top Gainers #{self.rank} - {self.company.symbol} - {self.date}"

class TopLosers(models.Model):
    date = models.DateField()
    rank = models.IntegerField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    change_percent = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField(null=True, blank=True)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ['date', 'rank', 'company']
        ordering = ['-date', 'rank']
    
    def __str__(self):
        return f"Top Losers #{self.rank} - {self.company.symbol} - {self.date}"