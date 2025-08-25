"""
Alpha Vantage API Client - Forex ve hisse senedi verileri
Alpha Vantage API entegrasyonu
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from .base_client import BaseAPIClient, RateLimit


class AlphaVantageClient(BaseAPIClient):
    """
    Alpha Vantage API Client
    
    Özellikler:
    - Forex real-time ve historical data
    - Stock fundamentals
    - Technical indicators
    - Economic indicators
    - Market news
    """
    
    def __init__(self, api_key: str = None):
        """
        Alpha Vantage client başlatma
        
        Args:
            api_key: Alpha Vantage API key
        """
        # Alpha Vantage rate limits: 5 calls per minute (free tier)
        rate_limit = RateLimit(calls_per_minute=5, calls_per_hour=500)
        
        super().__init__("https://www.alphavantage.co", api_key, rate_limit)
        
        # Supported forex pairs
        self.major_pairs = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 
            'USDCAD', 'NZDUSD', 'EURJPY', 'GBPJPY', 'EURGBP'
        ]
        
    def _get_auth_headers(self) -> Dict[str, str]:
        """Alpha Vantage auth headers"""
        return {}  # API key query parameter olarak gönderilir
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """
        Forex çifti güncel fiyatı
        
        Args:
            symbol: Forex çifti (örn: EURUSD)
            
        Returns:
            Güncel exchange rate
        """
        try:
            # Alpha Vantage forex format: FROM_SYMBOL=EUR&TO_SYMBOL=USD
            if len(symbol) == 6:  # EURUSD format
                from_symbol = symbol[:3]
                to_symbol = symbol[3:]
            else:
                # Already formatted or invalid
                return None
                
            params = {
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': from_symbol,
                'to_currency': to_symbol,
                'apikey': self.api_key or 'demo'
            }
            
            result = await self._make_request('GET', '/query', params=params)
            
            if result['success']:
                data = result['data']
                exchange_rate = data.get('Realtime Currency Exchange Rate', {})
                rate = exchange_rate.get('5. Exchange Rate')
                
                if rate:
                    return float(rate)
                    
        except Exception as e:
            self.logger.error(f"Error getting forex price for {symbol}: {str(e)}")
            
        return None
    
    async def get_historical_data(self, symbol: str, timeframe: str = 'daily',
                                limit: int = 100) -> Optional[List[Dict]]:
        """
        Forex geçmiş verileri
        
        Args:
            symbol: Forex çifti
            timeframe: 'intraday', 'daily', 'weekly', 'monthly'
            limit: Veri sayısı
            
        Returns:
            Historical forex data
        """
        try:
            if len(symbol) == 6:
                from_symbol = symbol[:3]
                to_symbol = symbol[3:]
            else:
                return None
                
            # Function mapping
            function_map = {
                'daily': 'FX_DAILY',
                'weekly': 'FX_WEEKLY',
                'monthly': 'FX_MONTHLY',
                'intraday': 'FX_INTRADAY'
            }
            
            function = function_map.get(timeframe, 'FX_DAILY')
            
            params = {
                'function': function,
                'from_symbol': from_symbol,
                'to_symbol': to_symbol,
                'apikey': self.api_key or 'demo'
            }
            
            if timeframe == 'intraday':
                params['interval'] = '60min'  # 1 hour intervals
                
            result = await self._make_request('GET', '/query', params=params)
            
            if result['success']:
                data = result['data']
                
                # Data key belirleme
                data_key = None
                for key in data.keys():
                    if 'Time Series' in key:
                        data_key = key
                        break
                
                if not data_key:
                    return None
                    
                time_series = data[data_key]
                
                # Format data
                formatted_data = []
                for date_str, values in list(time_series.items())[:limit]:
                    formatted_data.append({
                        'timestamp': datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S' 
                                                     if ' ' in date_str else '%Y-%m-%d'),
                        'open': float(values.get('1. open', 0)),
                        'high': float(values.get('2. high', 0)),
                        'low': float(values.get('3. low', 0)),
                        'close': float(values.get('4. close', 0)),
                        'volume': 0  # Forex'te volume yok
                    })
                
                # Tarihe göre sırala (en yeni en başta)
                formatted_data.sort(key=lambda x: x['timestamp'], reverse=True)
                
                return formatted_data
                
        except Exception as e:
            self.logger.error(f"Error getting historical forex data for {symbol}: {str(e)}")
            
        return None
    
    async def get_stock_fundamentals(self, symbol: str) -> Optional[Dict]:
        """
        Hisse senedi fundamental analizi
        
        Args:
            symbol: Hisse sembolü
            
        Returns:
            Fundamental data
        """
        try:
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': self.api_key or 'demo'
            }
            
            result = await self._make_request('GET', '/query', params=params)
            
            if result['success']:
                data = result['data']
                
                return {
                    'symbol': symbol,
                    'name': data.get('Name', 'N/A'),
                    'sector': data.get('Sector', 'N/A'),
                    'industry': data.get('Industry', 'N/A'),
                    'market_cap': self._safe_float(data.get('MarketCapitalization')),
                    'pe_ratio': self._safe_float(data.get('PERatio')),
                    'peg_ratio': self._safe_float(data.get('PEGRatio')),
                    'price_to_book': self._safe_float(data.get('PriceToBookRatio')),
                    'dividend_yield': self._safe_float(data.get('DividendYield')),
                    'eps': self._safe_float(data.get('EPS')),
                    'revenue_ttm': self._safe_float(data.get('RevenueTTM')),
                    'profit_margin': self._safe_float(data.get('ProfitMargin')),
                    'beta': self._safe_float(data.get('Beta')),
                    '52_week_high': self._safe_float(data.get('52WeekHigh')),
                    '52_week_low': self._safe_float(data.get('52WeekLow')),
                    'analyst_target': self._safe_float(data.get('AnalystTargetPrice'))
                }
                
        except Exception as e:
            self.logger.error(f"Error getting fundamentals for {symbol}: {str(e)}")
            
        return None
    
    async def get_technical_indicators(self, symbol: str, indicator: str,
                                     timeframe: str = 'daily', 
                                     period: int = 14) -> Optional[List[Dict]]:
        """
        Teknik indikatör verileri
        
        Args:
            symbol: Sembol (forex için EURUSD formatında)
            indicator: İndikatör adı (RSI, MACD, SMA, EMA, etc.)
            timeframe: Zaman dilimi
            period: İndikatör periyodu
            
        Returns:
            İndikatör verileri
        """
        try:
            # İndikatör function mapping
            indicator_functions = {
                'RSI': 'RSI',
                'MACD': 'MACD',
                'SMA': 'SMA',
                'EMA': 'EMA',
                'BBANDS': 'BBANDS',
                'STOCH': 'STOCH'
            }
            
            function = indicator_functions.get(indicator.upper())
            if not function:
                return None
                
            params = {
                'function': function,
                'symbol': symbol,
                'interval': 'daily',
                'time_period': period,
                'series_type': 'close',
                'apikey': self.api_key or 'demo'
            }
            
            result = await self._make_request('GET', '/query', params=params)
            
            if result['success']:
                data = result['data']
                
                # Technical Analysis data key bul
                data_key = None
                for key in data.keys():
                    if 'Technical Analysis' in key:
                        data_key = key
                        break
                
                if not data_key:
                    return None
                    
                indicator_data = data[data_key]
                
                # Format data
                formatted_data = []
                for date_str, values in list(indicator_data.items())[:100]:
                    formatted_entry = {
                        'timestamp': datetime.strptime(date_str, '%Y-%m-%d'),
                        'indicator': indicator.upper()
                    }
                    
                    # İndikatör değerlerini ekle
                    for value_key, value in values.items():
                        clean_key = value_key.split('. ')[-1].lower()
                        formatted_entry[clean_key] = float(value)
                    
                    formatted_data.append(formatted_entry)
                
                # Tarihe göre sırala
                formatted_data.sort(key=lambda x: x['timestamp'], reverse=True)
                
                return formatted_data
                
        except Exception as e:
            self.logger.error(f"Error getting {indicator} for {symbol}: {str(e)}")
            
        return None
    
    async def get_economic_indicators(self) -> Dict[str, Any]:
        """
        Ekonomik indikatörler
        
        Returns:
            Economic indicators data
        """
        indicators = {}
        
        try:
            # GDP
            gdp_result = await self._make_request('GET', '/query', {
                'function': 'REAL_GDP',
                'interval': 'quarterly',
                'apikey': self.api_key or 'demo'
            })
            
            if gdp_result['success']:
                indicators['gdp'] = gdp_result['data']
            
            # Inflation
            inflation_result = await self._make_request('GET', '/query', {
                'function': 'INFLATION',
                'apikey': self.api_key or 'demo'
            })
            
            if inflation_result['success']:
                indicators['inflation'] = inflation_result['data']
                
        except Exception as e:
            self.logger.error(f"Error getting economic indicators: {str(e)}")
            
        return indicators
    
    def _safe_float(self, value: Any) -> float:
        """Güvenli float dönüşümü"""
        try:
            if value is None or value == 'None' or value == '':
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    async def get_forex_majors(self) -> Dict[str, float]:
        """
        Major forex çiftleri fiyatları
        
        Returns:
            Major pairs dictionary
        """
        prices = {}
        
        # Rate limit nedeniyle concurrent requests sınırlı
        for pair in self.major_pairs[:5]:  # İlk 5 major pair
            price = await self.get_price(pair)
            if price:
                prices[pair] = price
                
            # Rate limit için bekleme
            await asyncio.sleep(12)  # 5 calls/minute = 12 seconds between calls
            
        return prices
    
    async def close(self) -> None:
        """Client kapatma"""
        await self._close_session()