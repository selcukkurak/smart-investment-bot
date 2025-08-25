"""
Smart Investment Bot - Binance Client
Cryptocurrency trading via Binance API
"""

import ccxt
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any


class BinanceClient:
    """
    Client for Binance cryptocurrency exchange
    """
    
    def __init__(self, api_key: str, secret_key: str, sandbox: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.sandbox = sandbox
        
        # Initialize CCXT Binance client
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret_key,
            'sandbox': sandbox,
            'enableRateLimit': True,
        })
        
    async def connect(self) -> bool:
        """Test connection to Binance"""
        try:
            if self.api_key and self.secret_key:
                balance = await self.get_account_balance()
                return balance is not None
            return True  # For sandbox/demo mode
        except Exception as e:
            print(f"Binance connection error: {e}")
            return False
    
    async def get_account_balance(self) -> Optional[Dict]:
        """Get account balance"""
        try:
            balance = self.exchange.fetch_balance()
            return {
                'total': balance.get('total', {}),
                'free': balance.get('free', {}),
                'used': balance.get('used', {}),
                'timestamp': datetime.now()
            }
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a trading pair"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
            return None
    
    def get_orderbook(self, symbol: str, limit: int = 10) -> Optional[Dict]:
        """Get order book data"""
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit)
            return {
                'symbol': symbol,
                'bids': orderbook['bids'][:limit],
                'asks': orderbook['asks'][:limit],
                'timestamp': datetime.now()
            }
        except Exception as e:
            print(f"Error getting orderbook for {symbol}: {e}")
            return None
    
    def get_klines(self, symbol: str, timeframe: str = "1h", 
                  limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Get candlestick data for technical analysis
        
        timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
        except Exception as e:
            print(f"Error getting klines for {symbol}: {e}")
            return None
    
    def place_market_order(self, symbol: str, side: str, amount: float,
                          test_mode: bool = True) -> Optional[Dict]:
        """
        Place a market order
        
        side: 'buy' or 'sell'
        amount: quantity to trade
        """
        try:
            if test_mode:
                # Simulate order for testing
                current_price = self.get_current_price(symbol)
                return {
                    'id': f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': current_price,
                    'cost': amount * current_price if current_price else 0,
                    'status': 'closed',
                    'timestamp': datetime.now(),
                    'test_mode': True
                }
            else:
                order = self.exchange.create_market_order(symbol, side, amount)
                return order
                
        except Exception as e:
            print(f"Error placing {side} order for {symbol}: {e}")
            return None
    
    def place_limit_order(self, symbol: str, side: str, amount: float,
                         price: float, test_mode: bool = True) -> Optional[Dict]:
        """
        Place a limit order
        """
        try:
            if test_mode:
                return {
                    'id': f"test_limit_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': price,
                    'cost': amount * price,
                    'status': 'open',
                    'timestamp': datetime.now(),
                    'test_mode': True
                }
            else:
                order = self.exchange.create_limit_order(symbol, side, amount, price)
                return order
                
        except Exception as e:
            print(f"Error placing limit {side} order for {symbol}: {e}")
            return None
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an open order"""
        try:
            if order_id.startswith('test_'):
                return True  # Test mode
            
            self.exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            print(f"Error cancelling order {order_id}: {e}")
            return False
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders"""
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            return orders
        except Exception as e:
            print(f"Error getting open orders: {e}")
            return []
    
    def get_trading_pairs(self) -> List[str]:
        """Get available trading pairs"""
        try:
            markets = self.exchange.load_markets()
            return list(markets.keys())
        except Exception as e:
            print(f"Error getting trading pairs: {e}")
            return []
    
    def get_24h_ticker(self, symbol: str) -> Optional[Dict]:
        """Get 24h ticker statistics"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'price': ticker['last'],
                'change': ticker['change'],
                'percentage': ticker['percentage'],
                'high': ticker['high'],
                'low': ticker['low'],
                'volume': ticker['quoteVolume'],
                'timestamp': datetime.now()
            }
        except Exception as e:
            print(f"Error getting 24h ticker for {symbol}: {e}")
            return None
    
    def get_account_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get recent trades for account"""
        try:
            trades = self.exchange.fetch_my_trades(symbol, limit=limit)
            return trades
        except Exception as e:
            print(f"Error getting trades for {symbol}: {e}")
            return []
    
    def calculate_trading_fees(self, symbol: str, amount: float, 
                             price: float) -> Dict[str, float]:
        """Calculate trading fees for a potential trade"""
        try:
            # Binance typical fees: 0.1% for spot trading
            maker_fee_rate = 0.001  # 0.1%
            taker_fee_rate = 0.001  # 0.1%
            
            trade_value = amount * price
            
            return {
                'maker_fee': trade_value * maker_fee_rate,
                'taker_fee': trade_value * taker_fee_rate,
                'fee_currency': symbol.split('/')[1] if '/' in symbol else 'USDT'
            }
        except Exception as e:
            print(f"Error calculating fees: {e}")
            return {'maker_fee': 0, 'taker_fee': 0, 'fee_currency': 'USDT'}