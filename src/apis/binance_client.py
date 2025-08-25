"""
Binance API Client - Kripto para işlemleri
CCXT kütüphanesi ile Binance entegrasyonu
"""

import ccxt.async_support as ccxt
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import hmac
import hashlib
import base64
import json

from .base_client import BaseAPIClient, RateLimit


class BinanceClient(BaseAPIClient):
    """
    Binance API Client
    
    Özellikler:
    - Spot ve futures trading
    - Real-time price data
    - Historical OHLCV data
    - Account information
    - Order management
    """
    
    def __init__(self, api_key: str = None, api_secret: str = None, 
                 testnet: bool = True):
        """
        Binance client başlatma
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Testnet kullanılsın mı
        """
        base_url = "https://testnet.binance.vision" if testnet else "https://api.binance.com"
        
        # Binance rate limits: 1200 requests per minute
        rate_limit = RateLimit(calls_per_minute=1200, calls_per_hour=10000)
        
        super().__init__(base_url, api_key, rate_limit)
        
        self.api_secret = api_secret
        self.testnet = testnet
        self.exchange = None
        
    async def _initialize_ccxt(self) -> None:
        """CCXT exchange başlatma"""
        if self.exchange is None:
            config = {
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'timeout': 30000,
                'enableRateLimit': True,
                'verbose': False
            }
            
            if self.testnet:
                config['sandbox'] = True
                
            self.exchange = ccxt.binance(config)
            
    def _get_auth_headers(self) -> Dict[str, str]:
        """Binance authentication headers"""
        if not self.api_key:
            return {}
            
        return {
            'X-MBX-APIKEY': self.api_key
        }
    
    def _generate_signature(self, query_string: str) -> str:
        """Binance signature oluşturma"""
        if not self.api_secret:
            return ""
            
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """
        Güncel fiyat alma
        
        Args:
            symbol: Sembol adı (örn: BTCUSDT)
            
        Returns:
            Güncel fiyat
        """
        try:
            await self._initialize_ccxt()
            ticker = await self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
            
        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {str(e)}")
            return None
    
    async def get_historical_data(self, symbol: str, timeframe: str = '1h',
                                limit: int = 100) -> Optional[List[Dict]]:
        """
        Geçmiş OHLCV verisi alma
        
        Args:
            symbol: Sembol adı
            timeframe: Zaman dilimi (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Veri sayısı
            
        Returns:
            OHLCV data list
        """
        try:
            await self._initialize_ccxt()
            
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Format data
            formatted_data = []
            for candle in ohlcv:
                formatted_data.append({
                    'timestamp': datetime.fromtimestamp(candle[0] / 1000),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                })
                
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return None
    
    async def get_account_balance(self) -> Optional[Dict]:
        """
        Hesap bakiyesi alma
        
        Returns:
            Account balance dictionary
        """
        try:
            await self._initialize_ccxt()
            balance = await self.exchange.fetch_balance()
            
            # Format balance data
            formatted_balance = {}
            for asset, amounts in balance.items():
                if asset not in ['info', 'free', 'used', 'total']:
                    if amounts['total'] > 0:
                        formatted_balance[asset] = {
                            'free': amounts['free'],
                            'used': amounts['used'],
                            'total': amounts['total']
                        }
            
            return formatted_balance
            
        except Exception as e:
            self.logger.error(f"Error getting account balance: {str(e)}")
            return None
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> Optional[Dict]:
        """
        Order book alma
        
        Args:
            symbol: Sembol adı
            limit: Derinlik limiti
            
        Returns:
            Order book data
        """
        try:
            await self._initialize_ccxt()
            order_book = await self.exchange.fetch_order_book(symbol, limit)
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'bids': order_book['bids'][:10],  # En iyi 10 bid
                'asks': order_book['asks'][:10],  # En iyi 10 ask
                'bid_price': order_book['bids'][0][0] if order_book['bids'] else 0,
                'ask_price': order_book['asks'][0][0] if order_book['asks'] else 0,
                'spread': (order_book['asks'][0][0] - order_book['bids'][0][0]) 
                         if order_book['bids'] and order_book['asks'] else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting order book for {symbol}: {str(e)}")
            return None
    
    async def place_order(self, symbol: str, order_type: str, side: str,
                         amount: float, price: float = None) -> Optional[Dict]:
        """
        Emir verme
        
        Args:
            symbol: Sembol adı
            order_type: 'market' veya 'limit'
            side: 'buy' veya 'sell'
            amount: Miktar
            price: Fiyat (limit order için)
            
        Returns:
            Order result
        """
        try:
            await self._initialize_ccxt()
            
            if order_type.lower() == 'market':
                if side.lower() == 'buy':
                    order = await self.exchange.create_market_buy_order(symbol, amount)
                else:
                    order = await self.exchange.create_market_sell_order(symbol, amount)
            else:  # limit order
                if not price:
                    raise ValueError("Price required for limit orders")
                    
                if side.lower() == 'buy':
                    order = await self.exchange.create_limit_buy_order(symbol, amount, price)
                else:
                    order = await self.exchange.create_limit_sell_order(symbol, amount, price)
            
            return {
                'success': True,
                'order_id': order['id'],
                'symbol': order['symbol'],
                'side': order['side'],
                'amount': order['amount'],
                'price': order['price'],
                'status': order['status'],
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error placing order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_order_status(self, order_id: str, symbol: str) -> Optional[Dict]:
        """
        Emir durumu kontrolü
        
        Args:
            order_id: Emir ID
            symbol: Sembol adı
            
        Returns:
            Order status
        """
        try:
            await self._initialize_ccxt()
            order = await self.exchange.fetch_order(order_id, symbol)
            
            return {
                'order_id': order['id'],
                'symbol': order['symbol'],
                'status': order['status'],
                'side': order['side'],
                'amount': order['amount'],
                'filled': order['filled'],
                'remaining': order['remaining'],
                'price': order['price'],
                'average_price': order['average'],
                'timestamp': order['timestamp']
            }
            
        except Exception as e:
            self.logger.error(f"Error getting order status: {str(e)}")
            return None
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Emir iptal etme
        
        Args:
            order_id: Emir ID
            symbol: Sembol adı
            
        Returns:
            İptal başarılı mı
        """
        try:
            await self._initialize_ccxt()
            await self.exchange.cancel_order(order_id, symbol)
            self.logger.info(f"Order {order_id} cancelled successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {str(e)}")
            return False
    
    async def get_trading_symbols(self) -> List[str]:
        """
        Trading sembolleri listesi
        
        Returns:
            Sembol listesi
        """
        try:
            await self._initialize_ccxt()
            markets = await self.exchange.fetch_markets()
            
            # Sadece aktif USDT çiftleri
            symbols = [
                market['symbol'] for market in markets 
                if market['active'] and market['quote'] == 'USDT'
            ]
            
            return sorted(symbols)
            
        except Exception as e:
            self.logger.error(f"Error getting trading symbols: {str(e)}")
            return []
    
    async def get_24h_ticker(self, symbol: str) -> Optional[Dict]:
        """
        24 saatlik ticker bilgisi
        
        Args:
            symbol: Sembol adı
            
        Returns:
            24h ticker data
        """
        try:
            await self._initialize_ccxt()
            ticker = await self.exchange.fetch_ticker(symbol)
            
            return {
                'symbol': ticker['symbol'],
                'price': ticker['last'],
                'change': ticker['change'],
                'percentage': ticker['percentage'],
                'high': ticker['high'],
                'low': ticker['low'],
                'volume': ticker['baseVolume'],
                'quote_volume': ticker['quoteVolume'],
                'timestamp': ticker['timestamp']
            }
            
        except Exception as e:
            self.logger.error(f"Error getting 24h ticker for {symbol}: {str(e)}")
            return None
    
    async def get_top_gainers_losers(self, limit: int = 10) -> Dict[str, List]:
        """
        En çok kazanan/kaybeden coinler
        
        Args:
            limit: Sonuç limiti
            
        Returns:
            {'gainers': [...], 'losers': [...]}
        """
        try:
            await self._initialize_ccxt()
            tickers = await self.exchange.fetch_tickers()
            
            # USDT çiftlerini filtrele ve sırala
            usdt_tickers = [
                {
                    'symbol': symbol,
                    'price': data['last'],
                    'change_pct': data['percentage']
                }
                for symbol, data in tickers.items()
                if symbol.endswith('/USDT') and data['percentage'] is not None
            ]
            
            # En çok kazananlar
            gainers = sorted(usdt_tickers, 
                           key=lambda x: x['change_pct'], reverse=True)[:limit]
            
            # En çok kaybedenler
            losers = sorted(usdt_tickers, 
                          key=lambda x: x['change_pct'])[:limit]
            
            return {
                'gainers': gainers,
                'losers': losers,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting gainers/losers: {str(e)}")
            return {'gainers': [], 'losers': []}
    
    async def close(self) -> None:
        """Client bağlantısını kapatma"""
        if self.exchange:
            await self.exchange.close()
            
        await self._close_session()