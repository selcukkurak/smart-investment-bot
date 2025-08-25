"""
Scalping Strategy - Hızlı alım-satım stratejisi
Kısa vadeli fiyat hareketlerinden kar elde etme
"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .base_strategy import BaseStrategy, Signal, SignalType


class ScalpingStrategy(BaseStrategy):
    """
    Scalping Trading Stratejisi
    
    Özellikler:
    - 1-5 dakikalık zaman dilimleri
    - Hızlı giriş/çıkış
    - Düşük risk, küçük karlılık
    - Volume analizi
    - RSI ve stochastic indikatörler
    """
    
    def __init__(self, timeframe: str = '5m'):
        """
        Scalping strategy başlatma
        
        Args:
            timeframe: Zaman dilimi (1m, 5m)
        """
        super().__init__("Scalping", timeframe)
        
        # Scalping parametreleri
        self.parameters = {
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'volume_multiplier': 1.5,  # Ortalama volume'un kaç katı gerekli
            'price_change_threshold': 0.002,  # %0.2 minimum fiyat değişimi
            'stop_loss_pct': 0.005,  # %0.5 stop loss
            'take_profit_pct': 0.010,  # %1.0 take profit
            'max_hold_time_minutes': 30,  # Maksimum tutma süresi
            'min_spread_pct': 0.001  # Minimum spread %0.1
        }
        
        self.min_confidence = 0.7  # Scalping için yüksek confidence gerekli
        
    async def analyze(self, symbol: str, historical_data: List[Dict],
                     current_price: float, **kwargs) -> Optional[Signal]:
        """
        Scalping analizi
        
        Args:
            symbol: Sembol adı
            historical_data: Geçmiş veri (minimum 20 candle)
            current_price: Güncel fiyat
            **kwargs: order_book, volume_data vb.
            
        Returns:
            Scalping sinyali
        """
        if not self.is_active or len(historical_data) < 20:
            return None
            
        try:
            # Data preparation
            closes = [d['close'] for d in historical_data]
            volumes = [d['volume'] for d in historical_data]
            highs = [d['high'] for d in historical_data]
            lows = [d['low'] for d in historical_data]
            
            # Technical indicators
            rsi = self._calculate_rsi(closes, period=14)
            stoch_k, stoch_d = self._calculate_stochastic(highs, lows, closes, period=14)
            sma_short = self._calculate_sma(closes, period=5)
            sma_long = self._calculate_sma(closes, period=20)
            
            # Volume analysis
            avg_volume = np.mean(volumes[-10:])  # Son 10 candle ortalaması
            current_volume = volumes[-1] if volumes else 0
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            # Price change analysis
            recent_change = (current_price - closes[-2]) / closes[-2] if len(closes) >= 2 else 0
            
            # Order book analysis (if available)
            order_book = kwargs.get('order_book')
            spread_ok = True
            if order_book:
                spread = order_book.get('spread', 0)
                spread_pct = spread / current_price if current_price > 0 else 1
                spread_ok = spread_pct <= self.parameters['min_spread_pct']
            
            # Signal generation
            signal = self._generate_scalping_signal(
                symbol, current_price, rsi, stoch_k, stoch_d,
                sma_short, sma_long, volume_ratio, recent_change, spread_ok
            )
            
            if signal:
                self.signals_generated += 1
                
            return signal
            
        except Exception as e:
            self.logger.error(f"Error in scalping analysis for {symbol}: {str(e)}")
            return None
    
    def _generate_scalping_signal(self, symbol: str, price: float, rsi: float,
                                stoch_k: float, stoch_d: float, sma_short: float,
                                sma_long: float, volume_ratio: float,
                                price_change: float, spread_ok: bool) -> Optional[Signal]:
        """Scalping sinyali oluşturma"""
        
        if not spread_ok:
            return None
            
        confidence = 0.0
        signal_type = SignalType.HOLD
        
        # Volume filter - yeterli volume var mı?
        if volume_ratio < self.parameters['volume_multiplier']:
            return None
        
        # BUY sinyali koşulları
        buy_conditions = [
            rsi < self.parameters['rsi_oversold'],  # RSI oversold
            stoch_k < 20 and stoch_d < 20,  # Stochastic oversold
            price > sma_short,  # Fiyat kısa SMA üzerinde
            price_change < -self.parameters['price_change_threshold'],  # Düşüş momentum
            volume_ratio >= self.parameters['volume_multiplier']  # Yüksek volume
        ]
        
        # SELL sinyali koşulları  
        sell_conditions = [
            rsi > self.parameters['rsi_overbought'],  # RSI overbought
            stoch_k > 80 and stoch_d > 80,  # Stochastic overbought
            price < sma_short,  # Fiyat kısa SMA altında
            price_change > self.parameters['price_change_threshold'],  # Yükseliş momentum
            volume_ratio >= self.parameters['volume_multiplier']  # Yüksek volume
        ]
        
        # BUY signal
        if sum(buy_conditions) >= 3:
            confidence = min(0.9, 0.5 + (sum(buy_conditions) * 0.1) + (volume_ratio * 0.1))
            signal_type = SignalType.STRONG_BUY if confidence > 0.8 else SignalType.BUY
            
        # SELL signal
        elif sum(sell_conditions) >= 3:
            confidence = min(0.9, 0.5 + (sum(sell_conditions) * 0.1) + (volume_ratio * 0.1))
            signal_type = SignalType.STRONG_SELL if confidence > 0.8 else SignalType.SELL
        
        # Trend confirmation
        if sma_short > sma_long and signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            confidence += 0.1  # Uptrend confirmation
        elif sma_short < sma_long and signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            confidence += 0.1  # Downtrend confirmation
        
        confidence = min(1.0, confidence)
        
        if signal_type != SignalType.HOLD and confidence >= self.min_confidence:
            signal = Signal(symbol, signal_type, confidence, price)
            
            # Metadata ekleme
            signal.add_metadata('rsi', rsi)
            signal.add_metadata('stoch_k', stoch_k)
            signal.add_metadata('volume_ratio', volume_ratio)
            signal.add_metadata('price_change', price_change)
            signal.add_metadata('strategy_type', 'scalping')
            
            return signal
            
        return None
    
    def get_risk_parameters(self, signal: Signal) -> Dict:
        """
        Scalping risk parametreleri
        
        Args:
            signal: Trading sinyali
            
        Returns:
            Risk parameters
        """
        if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            stop_loss_price = signal.price * (1 - self.parameters['stop_loss_pct'])
            take_profit_price = signal.price * (1 + self.parameters['take_profit_pct'])
        else:  # SELL signals
            stop_loss_price = signal.price * (1 + self.parameters['stop_loss_pct'])
            take_profit_price = signal.price * (1 - self.parameters['take_profit_pct'])
        
        # Position size - confidence bazlı
        base_position_pct = 0.05  # %5 base position
        confidence_multiplier = min(2.0, 1 + signal.confidence)
        position_size_pct = base_position_pct * confidence_multiplier
        
        return {
            'stop_loss_price': stop_loss_price,
            'take_profit_price': take_profit_price,
            'position_size_percentage': position_size_pct,
            'max_hold_time_minutes': self.parameters['max_hold_time_minutes'],
            'risk_reward_ratio': 2.0,  # 1:2 risk/reward
            'entry_type': 'market'  # Scalping için market order
        }
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """RSI hesaplama"""
        if len(prices) < period + 1:
            return 50  # Neutral RSI
            
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_stochastic(self, highs: List[float], lows: List[float],
                            closes: List[float], period: int = 14) -> tuple:
        """Stochastic oscillator hesaplama"""
        if len(closes) < period:
            return 50, 50
            
        recent_highs = highs[-period:]
        recent_lows = lows[-period:]
        current_close = closes[-1]
        
        highest_high = max(recent_highs)
        lowest_low = min(recent_lows)
        
        if highest_high == lowest_low:
            return 50, 50
            
        k_percent = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        
        # %D (3-period SMA of %K)
        if len(closes) >= period + 2:
            k_values = []
            for i in range(3):
                idx = -(i+1)
                period_highs = highs[idx-period+1:idx+1]
                period_lows = lows[idx-period+1:idx+1]
                period_close = closes[idx]
                
                if len(period_highs) == period:
                    h_high = max(period_highs)
                    l_low = min(period_lows)
                    if h_high != l_low:
                        k_val = ((period_close - l_low) / (h_high - l_low)) * 100
                        k_values.append(k_val)
                        
            d_percent = np.mean(k_values) if k_values else k_percent
        else:
            d_percent = k_percent
            
        return k_percent, d_percent
    
    def _calculate_sma(self, prices: List[float], period: int) -> float:
        """Simple Moving Average hesaplama"""
        if len(prices) < period:
            return prices[-1] if prices else 0
            
        return np.mean(prices[-period:])
    
    def optimize_parameters(self, backtest_results: List[Dict]) -> Dict:
        """
        Parameter optimizasyonu
        
        Args:
            backtest_results: Backtest sonuçları
            
        Returns:
            Optimize edilmiş parametreler
        """
        if not backtest_results:
            return self.parameters
            
        # En iyi performans gösteren parametre kombinasyonlarını bul
        best_win_rate = 0
        best_params = self.parameters.copy()
        
        # RSI threshold optimization
        for rsi_oversold in [25, 30, 35]:
            for rsi_overbought in [65, 70, 75]:
                for volume_mult in [1.2, 1.5, 2.0]:
                    
                    # Test parameters
                    test_params = self.parameters.copy()
                    test_params['rsi_oversold'] = rsi_oversold
                    test_params['rsi_overbought'] = rsi_overbought
                    test_params['volume_multiplier'] = volume_mult
                    
                    # Simulate performance with these parameters
                    win_rate = self._simulate_parameter_performance(
                        test_params, backtest_results
                    )
                    
                    if win_rate > best_win_rate:
                        best_win_rate = win_rate
                        best_params = test_params
        
        self.parameters = best_params
        self.logger.info(
            f"Parameters optimized - new win rate: {best_win_rate:.2%}"
        )
        
        return best_params
    
    def _simulate_parameter_performance(self, params: Dict, 
                                     backtest_data: List[Dict]) -> float:
        """Parameter performans simülasyonu"""
        # Basitleştirilmiş simülasyon
        # Gerçek uygulamada tam backtest yapılabilir
        
        wins = 0
        total = 0
        
        for data_point in backtest_data:
            rsi = data_point.get('rsi', 50)
            volume_ratio = data_point.get('volume_ratio', 1)
            actual_outcome = data_point.get('profitable', False)
            
            # Bu parametrelerle sinyal üretilir miydi?
            would_signal = (
                (rsi < params['rsi_oversold'] or rsi > params['rsi_overbought']) and
                volume_ratio >= params['volume_multiplier']
            )
            
            if would_signal:
                total += 1
                if actual_outcome:
                    wins += 1
                    
        return wins / total if total > 0 else 0
    
    def get_scalping_metrics(self, recent_trades: List[Dict]) -> Dict:
        """
        Scalping özel metrikleri
        
        Args:
            recent_trades: Son işlemler
            
        Returns:
            Scalping performance metrics
        """
        if not recent_trades:
            return {
                'average_hold_time': 0,
                'quick_profit_rate': 0,
                'volume_efficiency': 0
            }
            
        # Ortalama tutma süresi
        hold_times = []
        quick_profits = 0  # 5 dakika içinde kar eden işlemler
        
        for trade in recent_trades:
            if 'entry_time' in trade and 'exit_time' in trade:
                hold_time = (trade['exit_time'] - trade['entry_time']).total_seconds() / 60
                hold_times.append(hold_time)
                
                # Hızlı kar kontrolü
                if hold_time <= 5 and trade.get('profit', 0) > 0:
                    quick_profits += 1
        
        avg_hold_time = np.mean(hold_times) if hold_times else 0
        quick_profit_rate = quick_profits / len(recent_trades) if recent_trades else 0
        
        return {
            'average_hold_time_minutes': avg_hold_time,
            'quick_profit_rate': quick_profit_rate,
            'total_scalping_trades': len(recent_trades),
            'optimal_hold_time': avg_hold_time <= self.parameters['max_hold_time_minutes']
        }
    
    def adjust_for_market_conditions(self, market_volatility: float,
                                   trading_volume: float) -> None:
        """
        Piyasa koşullarına göre parametre ayarlama
        
        Args:
            market_volatility: Piyasa volatilitesi
            trading_volume: İşlem hacmi
        """
        # Yüksek volatilitede daha muhafazakar parametreler
        if market_volatility > 0.03:  # %3'ten fazla volatilite
            self.parameters['stop_loss_pct'] = 0.003  # Daha sıkı stop loss
            self.parameters['take_profit_pct'] = 0.006  # Daha düşük take profit
            self.parameters['min_confidence'] = 0.8  # Daha yüksek confidence
            
        # Düşük volatilitede daha agresif
        elif market_volatility < 0.01:  # %1'den az volatilite
            self.parameters['stop_loss_pct'] = 0.008  # Daha gevşek stop loss
            self.parameters['take_profit_pct'] = 0.015  # Daha yüksek take profit
            self.parameters['min_confidence'] = 0.6  # Daha düşük confidence
        
        # Volume bazlı ayarlama
        if trading_volume > 2.0:  # Yüksek volume
            self.parameters['volume_multiplier'] = 1.2  # Daha az volume gereksinimi
        else:
            self.parameters['volume_multiplier'] = 2.0  # Daha fazla volume gereksinimi
            
        self.logger.info(
            f"Parameters adjusted for market conditions: "
            f"volatility={market_volatility:.3f}, volume={trading_volume:.2f}"
        )
    
    def get_ideal_symbols(self, available_symbols: List[str],
                         symbol_data: Dict[str, Dict]) -> List[str]:
        """
        Scalping için ideal semboller
        
        Args:
            available_symbols: Mevcut semboller
            symbol_data: Sembol verileri (volume, volatility, spread)
            
        Returns:
            Scalping için uygun semboller
        """
        ideal_symbols = []
        
        for symbol in available_symbols:
            data = symbol_data.get(symbol, {})
            
            volume = data.get('volume', 0)
            volatility = data.get('volatility', 0)
            spread = data.get('spread_pct', 1)
            
            # Scalping kriterleri
            high_volume = volume > 1000000  # Yüksek volume
            good_volatility = 0.01 < volatility < 0.05  # %1-5 volatilite
            tight_spread = spread < 0.001  # %0.1'den az spread
            
            if high_volume and good_volatility and tight_spread:
                score = (volume / 1000000) + (1 / spread) + (volatility * 10)
                ideal_symbols.append((symbol, score))
        
        # Score'a göre sırala
        ideal_symbols.sort(key=lambda x: x[1], reverse=True)
        
        return [symbol for symbol, score in ideal_symbols[:10]]