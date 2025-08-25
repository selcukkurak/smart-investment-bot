"""
Market Scanner - Piyasa tarama algoritması
Otomatik fırsat tarama ve filtreleme
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging


@dataclass
class ScanCriteria:
    """Tarama kriterleri"""
    min_volume: float = 1000000
    min_price: float = 1.0
    max_price: float = 1000.0
    min_market_cap: float = 1000000
    rsi_oversold: float = 30
    rsi_overbought: float = 70
    volume_spike_ratio: float = 2.0
    price_change_threshold: float = 0.05


class MarketScanner:
    """
    Piyasa tarama sınıfı
    
    Özellikler:
    - Multi-asset scanning
    - Custom criteria filtering
    - Technical pattern detection
    - Volume analysis
    - Momentum screening
    """
    
    def __init__(self):
        self.logger = logging.getLogger('MarketScanner')
        self.scan_history = []
        self.watchlist = []
        
    async def scan_crypto_opportunities(self, api_client, 
                                      criteria: ScanCriteria = None) -> List[Dict]:
        """
        Kripto fırsatları tarama
        
        Args:
            api_client: Binance API client
            criteria: Tarama kriterleri
            
        Returns:
            Fırsat listesi
        """
        if criteria is None:
            criteria = ScanCriteria()
            
        opportunities = []
        
        try:
            # Trading symbols al
            symbols = await api_client.get_trading_symbols()
            
            # Major pairs ile başla (performans için)
            major_symbols = [s for s in symbols if any(pair in s for pair in 
                           ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT',
                            'SOL/USDT', 'AVAX/USDT', 'MATIC/USDT', 'LINK/USDT', 'UNI/USDT'])]
            
            # Paralel tarama
            scan_tasks = [
                self._scan_single_crypto(api_client, symbol, criteria) 
                for symbol in major_symbols[:20]  # İlk 20 major pair
            ]
            
            results = await asyncio.gather(*scan_tasks, return_exceptions=True)
            
            for symbol, result in zip(major_symbols[:20], results):
                if not isinstance(result, Exception) and result:
                    result['symbol'] = symbol
                    opportunities.append(result)
            
            # Score'a göre sırala
            opportunities.sort(key=lambda x: x.get('opportunity_score', 0), reverse=True)
            
            self.logger.info(f"🔍 Crypto scan completed: {len(opportunities)} opportunities found")
            
        except Exception as e:
            self.logger.error(f"Error in crypto scanning: {str(e)}")
            
        return opportunities[:10]  # En iyi 10 fırsat
    
    async def _scan_single_crypto(self, api_client, symbol: str, 
                                criteria: ScanCriteria) -> Optional[Dict]:
        """Tek kripto için tarama"""
        try:
            # Current price ve 24h ticker
            ticker = await api_client.get_24h_ticker(symbol)
            if not ticker:
                return None
                
            # Historical data
            historical = await api_client.get_historical_data(symbol, '1h', 100)
            if not historical or len(historical) < 50:
                return None
                
            # Filters
            if not self._apply_crypto_filters(ticker, criteria):
                return None
                
            # Technical analysis
            closes = [d['close'] for d in historical]
            
            # RSI
            rsi = self._calculate_simple_rsi(closes)
            
            # Volume analysis
            volumes = [d['volume'] for d in historical]
            avg_volume = np.mean(volumes[-20:])
            volume_ratio = ticker['volume'] / avg_volume if avg_volume > 0 else 1
            
            # Price momentum
            price_change_1h = (closes[-1] - closes[-2]) / closes[-2] if len(closes) >= 2 else 0
            price_change_4h = (closes[-1] - closes[-5]) / closes[-5] if len(closes) >= 5 else 0
            price_change_24h = ticker['percentage'] / 100
            
            # Opportunity scoring
            opportunity_score = self._calculate_crypto_opportunity_score(
                rsi, volume_ratio, price_change_1h, price_change_4h, 
                price_change_24h, ticker
            )
            
            if opportunity_score > 0.6:
                return {
                    'symbol': symbol,
                    'current_price': ticker['price'],
                    'rsi': rsi,
                    'volume_ratio': volume_ratio,
                    'price_change_1h': price_change_1h,
                    'price_change_4h': price_change_4h,
                    'price_change_24h': price_change_24h,
                    'opportunity_score': opportunity_score,
                    'volume_24h': ticker['volume'],
                    'scan_time': datetime.now(),
                    'criteria_met': True
                }
                
        except Exception as e:
            self.logger.error(f"Error scanning {symbol}: {str(e)}")
            
        return None
    
    def _apply_crypto_filters(self, ticker: Dict, criteria: ScanCriteria) -> bool:
        """Kripto filtrelerini uygulama"""
        # Price filter
        if ticker['price'] < criteria.min_price or ticker['price'] > criteria.max_price:
            return False
            
        # Volume filter
        if ticker['volume'] < criteria.min_volume:
            return False
            
        return True
    
    def _calculate_crypto_opportunity_score(self, rsi: float, volume_ratio: float,
                                          change_1h: float, change_4h: float,
                                          change_24h: float, ticker: Dict) -> float:
        """Kripto fırsat skoru hesaplama"""
        score = 0.0
        
        # RSI-based scoring
        if rsi < 30:  # Oversold
            score += 0.3
        elif rsi > 70:  # Overbought (short opportunity)
            score += 0.3
        elif 40 < rsi < 60:  # Neutral zone
            score += 0.1
            
        # Volume scoring
        if volume_ratio > 2.0:  # High volume spike
            score += 0.25
        elif volume_ratio > 1.5:
            score += 0.15
            
        # Momentum scoring
        momentum_score = abs(change_1h) + abs(change_4h) + abs(change_24h)
        if momentum_score > 0.05:  # Strong momentum
            score += 0.25
        elif momentum_score > 0.02:
            score += 0.15
            
        # Volatility bonus
        high_low_range = (ticker['high'] - ticker['low']) / ticker['price']
        if high_low_range > 0.05:  # Good volatility
            score += 0.1
            
        return min(1.0, score)
    
    async def scan_stock_opportunities(self, api_client, 
                                     criteria: ScanCriteria = None) -> List[Dict]:
        """
        Hisse fırsatları tarama
        
        Args:
            api_client: Yahoo Finance API client
            criteria: Tarama kriterleri
            
        Returns:
            Hisse fırsatları listesi
        """
        if criteria is None:
            criteria = ScanCriteria()
            
        opportunities = []
        
        try:
            # Popular stocks to scan
            popular_stocks = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
                'NFLX', 'AMD', 'CRM', 'PYPL', 'ADBE', 'INTC', 'CSCO',
                'ORCL', 'IBM', 'QCOM', 'TXN', 'AVGO', 'MU'
            ]
            
            # Paralel tarama
            scan_tasks = [
                self._scan_single_stock(api_client, symbol, criteria)
                for symbol in popular_stocks
            ]
            
            results = await asyncio.gather(*scan_tasks, return_exceptions=True)
            
            for symbol, result in zip(popular_stocks, results):
                if not isinstance(result, Exception) and result:
                    result['symbol'] = symbol
                    opportunities.append(result)
            
            # Score'a göre sırala
            opportunities.sort(key=lambda x: x.get('opportunity_score', 0), reverse=True)
            
            self.logger.info(f"📈 Stock scan completed: {len(opportunities)} opportunities found")
            
        except Exception as e:
            self.logger.error(f"Error in stock scanning: {str(e)}")
            
        return opportunities[:10]
    
    async def _scan_single_stock(self, api_client, symbol: str,
                               criteria: ScanCriteria) -> Optional[Dict]:
        """Tek hisse için tarama"""
        try:
            # Current price
            current_price = await api_client.get_price(symbol)
            if not current_price:
                return None
                
            # Company info
            company_info = await api_client.get_company_info(symbol)
            if not company_info:
                return None
                
            # Historical data
            historical = await api_client.get_historical_data(symbol, '1d', 100)
            if not historical or len(historical) < 50:
                return None
                
            # Filters
            if not self._apply_stock_filters(current_price, company_info, criteria):
                return None
                
            # Technical analysis
            closes = [d['close'] for d in historical]
            volumes = [d['volume'] for d in historical]
            
            rsi = self._calculate_simple_rsi(closes)
            
            # Volume analysis
            avg_volume = np.mean(volumes[-20:])
            recent_volume = volumes[-1] if volumes else 0
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            
            # Price changes
            price_change_1d = (closes[-1] - closes[-2]) / closes[-2] if len(closes) >= 2 else 0
            price_change_5d = (closes[-1] - closes[-6]) / closes[-6] if len(closes) >= 6 else 0
            
            # Fundamental scoring
            fundamental_score = self._calculate_fundamental_score(company_info)
            
            # Technical scoring
            technical_score = self._calculate_stock_technical_score(
                rsi, volume_ratio, price_change_1d, price_change_5d
            )
            
            # Combined opportunity score
            opportunity_score = (fundamental_score * 0.4) + (technical_score * 0.6)
            
            if opportunity_score > 0.6:
                return {
                    'symbol': symbol,
                    'current_price': current_price,
                    'rsi': rsi,
                    'volume_ratio': volume_ratio,
                    'price_change_1d': price_change_1d,
                    'price_change_5d': price_change_5d,
                    'opportunity_score': opportunity_score,
                    'fundamental_score': fundamental_score,
                    'technical_score': technical_score,
                    'market_cap': company_info['market_cap'],
                    'pe_ratio': company_info['pe_ratio'],
                    'sector': company_info['sector'],
                    'scan_time': datetime.now()
                }
                
        except Exception as e:
            self.logger.error(f"Error scanning stock {symbol}: {str(e)}")
            
        return None
    
    def _apply_stock_filters(self, price: float, company_info: Dict,
                           criteria: ScanCriteria) -> bool:
        """Hisse filtrelerini uygulama"""
        # Price filter
        if price < criteria.min_price or price > criteria.max_price:
            return False
            
        # Market cap filter
        market_cap = company_info.get('market_cap', 0)
        if market_cap < criteria.min_market_cap:
            return False
            
        return True
    
    def _calculate_fundamental_score(self, company_info: Dict) -> float:
        """Fundamental analiz skoru"""
        score = 0.5  # Base score
        
        # P/E ratio scoring
        pe_ratio = company_info.get('pe_ratio', 0)
        if 10 < pe_ratio < 25:  # Reasonable P/E
            score += 0.2
        elif pe_ratio > 0:  # At least positive earnings
            score += 0.1
            
        # Market cap scoring
        market_cap = company_info.get('market_cap', 0)
        if market_cap > 10_000_000_000:  # Large cap
            score += 0.1
        elif market_cap > 1_000_000_000:  # Mid cap
            score += 0.05
            
        # Dividend yield bonus
        dividend_yield = company_info.get('dividend_yield', 0)
        if dividend_yield > 0.02:  # >2% dividend
            score += 0.1
            
        # Beta scoring (volatility measure)
        beta = company_info.get('beta', 1)
        if 0.5 < beta < 1.5:  # Moderate volatility
            score += 0.1
            
        return min(1.0, score)
    
    def _calculate_stock_technical_score(self, rsi: float, volume_ratio: float,
                                       change_1d: float, change_5d: float) -> float:
        """Hisse teknik analiz skoru"""
        score = 0.0
        
        # RSI scoring
        if rsi < 30:  # Oversold opportunity
            score += 0.3
        elif rsi > 70:  # Overbought (short opportunity)
            score += 0.3
        elif 45 < rsi < 55:  # Neutral momentum
            score += 0.1
            
        # Volume scoring
        if volume_ratio > 2.0:
            score += 0.3
        elif volume_ratio > 1.5:
            score += 0.2
            
        # Momentum scoring
        if abs(change_1d) > 0.03:  # >3% daily move
            score += 0.2
        if abs(change_5d) > 0.10:  # >10% weekly move
            score += 0.2
            
        return min(1.0, score)
    
    async def scan_forex_opportunities(self, api_client,
                                     criteria: ScanCriteria = None) -> List[Dict]:
        """
        Forex fırsatları tarama
        
        Args:
            api_client: Alpha Vantage API client
            criteria: Tarama kriterleri
            
        Returns:
            Forex fırsatları
        """
        opportunities = []
        
        try:
            # Major forex pairs
            major_pairs = [
                'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD',
                'USDCAD', 'NZDUSD', 'EURJPY', 'GBPJPY', 'EURGBP'
            ]
            
            # Rate limit nedeniyle sequential scanning
            for pair in major_pairs[:5]:  # İlk 5 major pair
                opportunity = await self._scan_single_forex(api_client, pair, criteria)
                if opportunity:
                    opportunities.append(opportunity)
                    
                # Rate limit için bekleme
                await asyncio.sleep(12)  # Alpha Vantage: 5 calls/minute
            
            # Score'a göre sırala
            opportunities.sort(key=lambda x: x.get('opportunity_score', 0), reverse=True)
            
            self.logger.info(f"💱 Forex scan completed: {len(opportunities)} opportunities found")
            
        except Exception as e:
            self.logger.error(f"Error in forex scanning: {str(e)}")
            
        return opportunities
    
    async def _scan_single_forex(self, api_client, pair: str,
                               criteria: ScanCriteria) -> Optional[Dict]:
        """Tek forex çifti için tarama"""
        try:
            # Current price
            current_price = await api_client.get_price(pair)
            if not current_price:
                return None
                
            # Historical data
            historical = await api_client.get_historical_data(pair, 'daily', 50)
            if not historical or len(historical) < 30:
                return None
                
            closes = [d['close'] for d in historical]
            
            # Technical indicators
            rsi = self._calculate_simple_rsi(closes)
            
            # Volatility analysis
            volatility = np.std(closes[-20:]) / np.mean(closes[-20:])
            
            # Trend analysis
            sma_10 = np.mean(closes[-10:])
            sma_30 = np.mean(closes[-30:])
            trend_strength = abs(sma_10 - sma_30) / sma_30
            
            # Price changes
            change_1d = (closes[-1] - closes[-2]) / closes[-2] if len(closes) >= 2 else 0
            change_1w = (closes[-1] - closes[-8]) / closes[-8] if len(closes) >= 8 else 0
            
            # Opportunity scoring
            opportunity_score = self._calculate_forex_opportunity_score(
                rsi, volatility, trend_strength, change_1d, change_1w
            )
            
            if opportunity_score > 0.5:
                return {
                    'symbol': pair,
                    'current_price': current_price,
                    'rsi': rsi,
                    'volatility': volatility,
                    'trend_strength': trend_strength,
                    'change_1d': change_1d,
                    'change_1w': change_1w,
                    'opportunity_score': opportunity_score,
                    'scan_time': datetime.now()
                }
                
        except Exception as e:
            self.logger.error(f"Error scanning forex {pair}: {str(e)}")
            
        return None
    
    def _calculate_forex_opportunity_score(self, rsi: float, volatility: float,
                                         trend_strength: float, change_1d: float,
                                         change_1w: float) -> float:
        """Forex fırsat skoru hesaplama"""
        score = 0.0
        
        # RSI scoring
        if rsi < 30 or rsi > 70:  # Extreme levels
            score += 0.3
        elif 35 < rsi < 65:  # Moderate levels
            score += 0.1
            
        # Volatility scoring (forex için optimal volatilite)
        if 0.005 < volatility < 0.02:  # %0.5-2% volatility
            score += 0.3
        elif volatility > 0.02:  # High volatility
            score += 0.2
            
        # Trend strength scoring
        if trend_strength > 0.01:  # Strong trend
            score += 0.2
        elif trend_strength > 0.005:  # Moderate trend
            score += 0.1
            
        # Recent movement scoring
        if abs(change_1d) > 0.005:  # >0.5% daily move
            score += 0.1
        if abs(change_1w) > 0.02:  # >2% weekly move
            score += 0.1
            
        return min(1.0, score)
    
    def _calculate_simple_rsi(self, prices: List[float], period: int = 14) -> float:
        """Basit RSI hesaplama (son değer)"""
        if len(prices) < period + 1:
            return 50.0
            
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def create_custom_scan(self, name: str, criteria: Dict) -> str:
        """
        Custom tarama oluşturma
        
        Args:
            name: Tarama adı
            criteria: Custom criteria
            
        Returns:
            Scan ID
        """
        scan_id = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        custom_scan = {
            'id': scan_id,
            'name': name,
            'criteria': criteria,
            'created_at': datetime.now(),
            'results': []
        }
        
        self.scan_history.append(custom_scan)
        
        self.logger.info(f"Custom scan created: {name} (ID: {scan_id})")
        
        return scan_id
    
    def add_to_watchlist(self, symbol: str, reason: str = "") -> bool:
        """
        Watchlist'e sembol ekleme
        
        Args:
            symbol: Sembol adı
            reason: Ekleme nedeni
            
        Returns:
            Ekleme başarılı mı
        """
        if symbol not in [w['symbol'] for w in self.watchlist]:
            self.watchlist.append({
                'symbol': symbol,
                'added_at': datetime.now(),
                'reason': reason,
                'alerts_enabled': True
            })
            
            self.logger.info(f"Added {symbol} to watchlist: {reason}")
            return True
            
        return False
    
    def remove_from_watchlist(self, symbol: str) -> bool:
        """
        Watchlist'ten sembol çıkarma
        
        Args:
            symbol: Sembol adı
            
        Returns:
            Çıkarma başarılı mı
        """
        self.watchlist = [w for w in self.watchlist if w['symbol'] != symbol]
        self.logger.info(f"Removed {symbol} from watchlist")
        return True
    
    async def scan_watchlist(self, api_clients: Dict) -> List[Dict]:
        """
        Watchlist tarama
        
        Args:
            api_clients: API client'ları
            
        Returns:
            Watchlist analiz sonuçları
        """
        results = []
        
        for item in self.watchlist:
            symbol = item['symbol']
            
            try:
                # Asset type belirleme
                if '/' in symbol or symbol.endswith('USDT'):
                    # Crypto
                    client = api_clients.get('binance')
                    if client:
                        price = await client.get_price(symbol)
                        ticker = await client.get_24h_ticker(symbol)
                        
                        if price and ticker:
                            results.append({
                                'symbol': symbol,
                                'asset_type': 'crypto',
                                'current_price': price,
                                'change_24h': ticker['percentage'],
                                'volume': ticker['volume'],
                                'watchlist_reason': item['reason'],
                                'scan_time': datetime.now()
                            })
                            
                elif len(symbol) == 6 and symbol.isupper():
                    # Forex
                    client = api_clients.get('alpha_vantage')
                    if client:
                        price = await client.get_price(symbol)
                        
                        if price:
                            results.append({
                                'symbol': symbol,
                                'asset_type': 'forex',
                                'current_price': price,
                                'watchlist_reason': item['reason'],
                                'scan_time': datetime.now()
                            })
                            
                else:
                    # Stock
                    client = api_clients.get('yahoo_finance')
                    if client:
                        price = await client.get_price(symbol)
                        
                        if price:
                            results.append({
                                'symbol': symbol,
                                'asset_type': 'stock',
                                'current_price': price,
                                'watchlist_reason': item['reason'],
                                'scan_time': datetime.now()
                            })
                
            except Exception as e:
                self.logger.error(f"Error scanning watchlist item {symbol}: {str(e)}")
                
        return results
    
    def get_scan_summary(self) -> Dict:
        """
        Tarama özeti
        
        Returns:
            Tarama istatistikleri
        """
        total_scans = len(self.scan_history)
        watchlist_size = len(self.watchlist)
        
        # Son tarama sonuçları
        recent_opportunities = 0
        if self.scan_history:
            recent_scan = self.scan_history[-1]
            recent_opportunities = len(recent_scan.get('results', []))
        
        return {
            'total_scans_performed': total_scans,
            'watchlist_size': watchlist_size,
            'recent_opportunities_found': recent_opportunities,
            'last_scan_time': self.scan_history[-1]['created_at'] if self.scan_history else None,
            'scan_types_available': ['crypto', 'stocks', 'forex', 'custom', 'watchlist']
        }