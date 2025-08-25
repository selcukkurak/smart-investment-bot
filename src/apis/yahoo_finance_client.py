"""
Yahoo Finance API Client - Hisse senedi ve global piyasa verileri
yfinance kütüphanesi ile entegrasyon
"""

import yfinance as yf
import pandas as pd
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import concurrent.futures

from .base_client import BaseAPIClient, RateLimit


class YahooFinanceClient(BaseAPIClient):
    """
    Yahoo Finance API Client
    
    Özellikler:
    - Hisse senedi fiyatları
    - Index verileri (S&P 500, NASDAQ, etc.)
    - Company fundamentals
    - Historical data
    - Market news
    """
    
    def __init__(self):
        """Yahoo Finance client başlatma"""
        # Yahoo Finance ücretsiz olduğu için rate limit gevşek
        rate_limit = RateLimit(calls_per_minute=120, calls_per_hour=2000)
        
        super().__init__("https://query1.finance.yahoo.com", None, rate_limit)
        
        # Thread pool for sync yfinance operations
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        
    def _get_auth_headers(self) -> Dict[str, str]:
        """Yahoo Finance auth headers (not required)"""
        return {}
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """
        Güncel hisse fiyatı alma
        
        Args:
            symbol: Hisse sembolü (örn: AAPL, MSFT)
            
        Returns:
            Güncel fiyat
        """
        try:
            loop = asyncio.get_event_loop()
            
            def fetch_price():
                ticker = yf.Ticker(symbol)
                info = ticker.info
                return info.get('currentPrice') or info.get('regularMarketPrice')
            
            price = await loop.run_in_executor(self.executor, fetch_price)
            return float(price) if price else None
            
        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {str(e)}")
            return None
    
    async def get_historical_data(self, symbol: str, timeframe: str = '1d',
                                limit: int = 100) -> Optional[List[Dict]]:
        """
        Geçmiş hisse verisi alma
        
        Args:
            symbol: Hisse sembolü
            timeframe: Zaman dilimi (1d, 1wk, 1mo)
            limit: Gün sayısı
            
        Returns:
            Historical data list
        """
        try:
            loop = asyncio.get_event_loop()
            
            def fetch_historical():
                ticker = yf.Ticker(symbol)
                
                # Period mapping
                period_map = {
                    '1d': f'{limit}d',
                    '1wk': f'{min(limit, 52)}wk',
                    '1mo': f'{min(limit, 24)}mo'
                }
                
                period = period_map.get(timeframe, f'{limit}d')
                hist = ticker.history(period=period)
                
                return hist
            
            hist_data = await loop.run_in_executor(self.executor, fetch_historical)
            
            if hist_data.empty:
                return None
                
            # Format data
            formatted_data = []
            for index, row in hist_data.iterrows():
                formatted_data.append({
                    'timestamp': index.to_pydatetime(),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': float(row['Volume'])
                })
                
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return None
    
    async def get_company_info(self, symbol: str) -> Optional[Dict]:
        """
        Şirket bilgileri alma
        
        Args:
            symbol: Hisse sembolü
            
        Returns:
            Company information
        """
        try:
            loop = asyncio.get_event_loop()
            
            def fetch_info():
                ticker = yf.Ticker(symbol)
                return ticker.info
            
            info = await loop.run_in_executor(self.executor, fetch_info)
            
            return {
                'symbol': symbol,
                'company_name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                '52_week_low': info.get('fiftyTwoWeekLow', 0),
                'average_volume': info.get('averageVolume', 0),
                'description': info.get('longBusinessSummary', 'N/A')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting company info for {symbol}: {str(e)}")
            return None
    
    async def get_market_indices(self) -> Dict[str, Dict]:
        """
        Piyasa endeksleri bilgileri
        
        Returns:
            Market indices data
        """
        indices = {
            '^GSPC': 'S&P 500',
            '^IXIC': 'NASDAQ',
            '^DJI': 'Dow Jones',
            '^VIX': 'VIX',
            '^TNX': '10-Year Treasury'
        }
        
        results = {}
        
        try:
            for symbol, name in indices.items():
                price = await self.get_price(symbol)
                
                if price:
                    # 1 günlük değişim için historical data al
                    hist_data = await self.get_historical_data(symbol, '1d', 2)
                    
                    change = 0
                    change_pct = 0
                    
                    if hist_data and len(hist_data) >= 2:
                        yesterday_close = hist_data[-2]['close']
                        today_price = price
                        change = today_price - yesterday_close
                        change_pct = (change / yesterday_close) * 100
                    
                    results[symbol] = {
                        'name': name,
                        'price': price,
                        'change': change,
                        'change_percentage': change_pct,
                        'timestamp': datetime.now()
                    }
        
        except Exception as e:
            self.logger.error(f"Error getting market indices: {str(e)}")
            
        return results
    
    async def get_trending_stocks(self, country: str = 'US') -> List[Dict]:
        """
        Trend olan hisseler
        
        Args:
            country: Ülke kodu (US, TR, etc.)
            
        Returns:
            Trending stocks list
        """
        try:
            # Yahoo Finance'da trend hisseleri için popüler semboller
            if country.upper() == 'US':
                trending_symbols = [
                    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
                    'NVDA', 'META', 'NFLX', 'AMD', 'CRM'
                ]
            elif country.upper() == 'TR':
                trending_symbols = [
                    'BIST.IS', 'THYAO.IS', 'ASELS.IS', 'SASA.IS', 'EREGL.IS'
                ]
            else:
                trending_symbols = ['AAPL', 'MSFT', 'GOOGL']
            
            results = []
            
            for symbol in trending_symbols:
                price = await self.get_price(symbol)
                if price:
                    # Volume ve değişim bilgisi için historical data
                    hist_data = await self.get_historical_data(symbol, '1d', 2)
                    
                    volume = 0
                    change_pct = 0
                    
                    if hist_data and len(hist_data) >= 1:
                        volume = hist_data[-1]['volume']
                        if len(hist_data) >= 2:
                            yesterday_close = hist_data[-2]['close']
                            change_pct = ((price - yesterday_close) / yesterday_close) * 100
                    
                    results.append({
                        'symbol': symbol,
                        'price': price,
                        'change_percentage': change_pct,
                        'volume': volume,
                        'country': country
                    })
            
            # Değişim yüzdesine göre sırala
            results.sort(key=lambda x: abs(x['change_percentage']), reverse=True)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting trending stocks: {str(e)}")
            return []
    
    async def search_stocks(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Hisse arama
        
        Args:
            query: Arama terimi
            limit: Sonuç limiti
            
        Returns:
            Arama sonuçları
        """
        try:
            # yfinance ile doğrudan arama API'si yok, bu yüzden bilinen sembollerden ara
            # Gerçek uygulamada Yahoo Finance arama API'si kullanılabilir
            
            common_stocks = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
                'NFLX', 'AMD', 'CRM', 'PYPL', 'ADBE', 'INTC', 'CSCO'
            ]
            
            # Query'ye uygun semboller bul
            matching_symbols = [
                symbol for symbol in common_stocks
                if query.upper() in symbol or symbol in query.upper()
            ]
            
            results = []
            
            for symbol in matching_symbols[:limit]:
                info = await self.get_company_info(symbol)
                if info:
                    price = await self.get_price(symbol)
                    
                    results.append({
                        'symbol': symbol,
                        'name': info['company_name'],
                        'price': price,
                        'sector': info['sector'],
                        'market_cap': info['market_cap']
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching stocks: {str(e)}")
            return []
    
    async def close(self) -> None:
        """Client kapatma"""
        if self.executor:
            self.executor.shutdown(wait=True)
            
        await self._close_session()