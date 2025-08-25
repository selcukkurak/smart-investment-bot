"""
Smart Investment Bot - Simplified Yahoo Finance Client
Uses only standard library for basic market data
"""

import urllib.request
import urllib.parse
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import io


class SimpleYahooFinanceClient:
    """
    Simplified Yahoo Finance client using only standard library
    """
    
    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart/"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol using Yahoo Finance API"""
        try:
            url = f"{self.base_url}{symbol}?interval=1m&range=1d"
            
            request = urllib.request.Request(url)
            request.add_header('User-Agent', self.user_agent)
            
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            # Extract price from Yahoo Finance response
            chart = data.get('chart', {})
            if chart.get('result'):
                result = chart['result'][0]
                meta = result.get('meta', {})
                current_price = meta.get('regularMarketPrice')
                
                if current_price:
                    return float(current_price)
        
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
        
        return None
    
    def get_simple_data(self, symbol: str) -> Optional[Dict]:
        """Get basic market data for a symbol"""
        try:
            url = f"{self.base_url}{symbol}?interval=1d&range=5d"
            
            request = urllib.request.Request(url)
            request.add_header('User-Agent', self.user_agent)
            
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            chart = data.get('chart', {})
            if chart.get('result'):
                result = chart['result'][0]
                meta = result.get('meta', {})
                timestamps = result.get('timestamp', [])
                quotes = result.get('indicators', {}).get('quote', [{}])[0]
                
                if timestamps and quotes:
                    closes = quotes.get('close', [])
                    volumes = quotes.get('volume', [])
                    
                    # Get recent data
                    current_price = closes[-1] if closes else None
                    prev_price = closes[-2] if len(closes) > 1 else current_price
                    volume = volumes[-1] if volumes else 0
                    
                    change_24h = 0
                    if prev_price and current_price:
                        change_24h = ((current_price - prev_price) / prev_price) * 100
                    
                    return {
                        'symbol': symbol,
                        'current_price': current_price,
                        'change_24h': change_24h,
                        'volume': volume,
                        'timestamp': datetime.now(),
                        'meta': meta
                    }
        
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
        
        return None
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Get current prices for multiple symbols"""
        prices = {}
        for symbol in symbols:
            prices[symbol] = self.get_current_price(symbol)
        return prices