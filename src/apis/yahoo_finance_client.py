"""
Smart Investment Bot - Yahoo Finance Client
Free market data API for stocks, forex, and commodities
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp


class YahooFinanceClient:
    """
    Client for Yahoo Finance API - provides free market data
    """
    
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                return float(data['Close'].iloc[-1])
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
        return None
    
    def get_historical_data(self, symbol: str, period: str = "1mo",
                           interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Get historical data for technical analysis
        
        period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            return data
        except Exception as e:
            print(f"Error getting historical data for {symbol}: {e}")
        return None
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Get current prices for multiple symbols"""
        prices = {}
        for symbol in symbols:
            prices[symbol] = self.get_current_price(symbol)
        return prices
    
    def get_asset_info(self, symbol: str) -> Optional[Dict]:
        """Get detailed asset information"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'volume': info.get('volume', 0),
                'avg_volume': info.get('averageVolume', 0),
                'beta': info.get('beta', 0),
                'pe_ratio': info.get('trailingPE', 0),
                '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                '52_week_low': info.get('fiftyTwoWeekLow', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'current_price': info.get('currentPrice', 0)
            }
        except Exception as e:
            print(f"Error getting asset info for {symbol}: {e}")
        return None
    
    def get_market_movers(self, market: str = "US") -> Dict[str, List[Dict]]:
        """
        Get market movers (gainers, losers, most active)
        """
        try:
            # Popular US stocks for demonstration
            popular_symbols = [
                'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 
                'META', 'NVDA', 'NFLX', 'CRM', 'ADBE'
            ]
            
            movers = {'gainers': [], 'losers': [], 'most_active': []}
            
            for symbol in popular_symbols:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                
                if len(hist) >= 2:
                    prev_close = hist['Close'].iloc[-2]
                    current_close = hist['Close'].iloc[-1]
                    change_percent = ((current_close - prev_close) / prev_close) * 100
                    volume = hist['Volume'].iloc[-1]
                    
                    stock_data = {
                        'symbol': symbol,
                        'current_price': current_close,
                        'change_percent': change_percent,
                        'volume': volume
                    }
                    
                    if change_percent > 2:
                        movers['gainers'].append(stock_data)
                    elif change_percent < -2:
                        movers['losers'].append(stock_data)
                    
                    movers['most_active'].append(stock_data)
            
            # Sort results
            movers['gainers'].sort(key=lambda x: x['change_percent'], reverse=True)
            movers['losers'].sort(key=lambda x: x['change_percent'])
            movers['most_active'].sort(key=lambda x: x['volume'], reverse=True)
            
            return movers
            
        except Exception as e:
            print(f"Error getting market movers: {e}")
            return {'gainers': [], 'losers': [], 'most_active': []}
    
    def get_volatility(self, symbol: str, days: int = 30) -> Optional[float]:
        """Calculate volatility (standard deviation of returns)"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=f"{days}d")
            
            if len(data) > 1:
                # Calculate daily returns
                returns = data['Close'].pct_change().dropna()
                # Calculate volatility (annualized)
                volatility = returns.std() * (252 ** 0.5)  # 252 trading days per year
                return float(volatility)
        except Exception as e:
            print(f"Error calculating volatility for {symbol}: {e}")
        return None
    
    def scan_markets(self, asset_types: List[str]) -> Dict[str, List[Dict]]:
        """
        Scan different markets for trading opportunities
        """
        opportunities = {}
        
        # Define symbols for different asset types
        symbols_map = {
            'stocks': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'],
            'forex': ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X'],
            'commodities': ['GC=F', 'CL=F', 'SI=F'],  # Gold, Oil, Silver
            'crypto': ['BTC-USD', 'ETH-USD', 'BNB-USD']
        }
        
        for asset_type in asset_types:
            if asset_type in symbols_map:
                opportunities[asset_type] = []
                
                for symbol in symbols_map[asset_type]:
                    try:
                        # Get recent data for analysis
                        ticker = yf.Ticker(symbol)
                        data = ticker.history(period="5d", interval="1h")
                        
                        if len(data) > 24:  # At least 24 hours of data
                            current_price = data['Close'].iloc[-1]
                            price_24h_ago = data['Close'].iloc[-24]
                            change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
                            
                            # Calculate simple momentum indicator
                            sma_24 = data['Close'].tail(24).mean()
                            momentum = ((current_price - sma_24) / sma_24) * 100
                            
                            volume_avg = data['Volume'].tail(24).mean()
                            current_volume = data['Volume'].iloc[-1]
                            volume_ratio = current_volume / volume_avg if volume_avg > 0 else 1
                            
                            opportunity = {
                                'symbol': symbol,
                                'current_price': float(current_price),
                                'change_24h': float(change_24h),
                                'momentum': float(momentum),
                                'volume_ratio': float(volume_ratio),
                                'volatility': self.get_volatility(symbol, 7),
                                'last_updated': datetime.now()
                            }
                            
                            opportunities[asset_type].append(opportunity)
                    
                    except Exception as e:
                        print(f"Error scanning {symbol}: {e}")
        
        return opportunities
    
    def get_technical_indicators(self, symbol: str, period: str = "3mo") -> Optional[Dict]:
        """
        Calculate basic technical indicators
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if len(data) < 50:  # Need enough data for indicators
                return None
            
            # Simple Moving Averages
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            
            # Relative Strength Index (RSI) - simplified
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            sma_20 = data['Close'].rolling(window=20).mean()
            std_20 = data['Close'].rolling(window=20).std()
            data['BB_Upper'] = sma_20 + (std_20 * 2)
            data['BB_Lower'] = sma_20 - (std_20 * 2)
            
            # Get latest values
            latest = data.iloc[-1]
            
            return {
                'symbol': symbol,
                'current_price': float(latest['Close']),
                'sma_20': float(latest['SMA_20']) if not pd.isna(latest['SMA_20']) else None,
                'sma_50': float(latest['SMA_50']) if not pd.isna(latest['SMA_50']) else None,
                'rsi': float(latest['RSI']) if not pd.isna(latest['RSI']) else None,
                'bb_upper': float(latest['BB_Upper']) if not pd.isna(latest['BB_Upper']) else None,
                'bb_lower': float(latest['BB_Lower']) if not pd.isna(latest['BB_Lower']) else None,
                'volume': float(latest['Volume']),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error calculating technical indicators for {symbol}: {e}")
        return None