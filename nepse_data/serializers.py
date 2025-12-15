# nepse_data/serializers.py
from rest_framework import serializers
from .models import DailyStockData, Company, IndexData, TopGainers, TopLosers

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'symbol', 'name', 'sector', 'instrument_type']

class StockDataSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    symbol = serializers.CharField(source='company.symbol', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    sector = serializers.CharField(source='company.sector', read_only=True)
    
    class Meta:
        model = DailyStockData
        fields = [
            'id', 'symbol', 'company_name', 'sector', 'company', 'date',
            'open_price', 'high_price', 'low_price', 'close_price',
            'volume', 'change', 'change_percent', 'last_updated'
        ]

class TopGainersSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source='company.symbol', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    sector = serializers.CharField(source='company.sector', read_only=True)
    
    class Meta:
        model = TopGainers
        fields = ['date', 'rank', 'symbol', 'company_name', 'change_percent', 
                'volume', 'close_price', 'sector']

class TopLosersSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source='company.symbol', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    sector = serializers.CharField(source='company.sector', read_only=True)
    
    class Meta:
        model = TopLosers
        fields = ['date', 'rank', 'symbol', 'company_name', 'change_percent', 
                'volume', 'close_price', 'sector']