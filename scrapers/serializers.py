# scrapers/serializers.py
from rest_framework import serializers
from .models import StockData, Company, MarketStatus
from django.utils import timezone

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'symbol', 'name', 'sector', 'listed_shares', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class StockDataSerializer(serializers.ModelSerializer):
    # Clean API response - only real data
    id = serializers.IntegerField(read_only=True)
    symbol = serializers.CharField(read_only=True, source='company.symbol')
    company_name = serializers.CharField(read_only=True, source='company.name')
    
    class Meta:
        model = StockData
        fields = [
            # Identification
            'id', 'symbol', 'company_name',
            
            # ✅ ACTUAL PRICE DATA (from unofficial API)
            'close_price', 'last_traded_price',
            
            # ✅ ACTUAL CHANGE DATA (from unofficial API)
            'previous_close', 'difference', 'percentage_change',
            
            # Metadata
            'scrape_date', 'scrape_time', 'data_source', 'is_closing_data',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def to_representation(self, instance):
        """Convert Decimal to float for JSON"""
        representation = super().to_representation(instance)
        
        # Convert Decimal fields to float
        decimal_fields = [
            'close_price', 'last_traded_price',
            'previous_close', 'difference', 'percentage_change'
        ]
        
        for field in decimal_fields:
            if field in representation and representation[field] is not None:
                representation[field] = float(representation[field])
        
        # Format dates
        if 'scrape_date' in representation:
            representation['scrape_date'] = instance.scrape_date.strftime('%Y-%m-%d')
        
        return representation

class MarketStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketStatus
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['total_turnover'] = float(instance.total_turnover) if instance.total_turnover else 0
        return representation