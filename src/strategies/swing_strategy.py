"""
Swing Trading Strategy - Orta vadeli swing trading
Trend değişimlerini yakalayarak kar elde etme
"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .base_strategy import BaseStrategy, Signal, SignalType


class SwingStrategy(BaseStrategy):
    """
    Swing Trading Stratejisi
    
    Özellikler:
    - 4h-1d zaman dilimleri
    - Trend reversal yakalama
    - Orta vadeli pozisyonlar (1-7 gün)
    - Moving averages ve momentum
    - MACD ve Bollinger Bands
    """
    
    def __init__(self, timeframe: str = '4h'):
        """
        Swing strategy başlatma
        
        Args:
            timeframe: Zaman dilimi (4h, 1d)
        """
        super().__init__("Swing", timeframe)
        
        # Swing trading parametreleri
        self.parameters = {
            'ema_short': 12,  # Kısa EMA
            'ema_long': 26,   # Uzun EMA
            'rsi_oversold': 35,
            'rsi_overbought': 65,
            'macd_signal_period': 9,
            'bollinger_period': 20,
            'bollinger_std': 2,
            'volume_confirmation': True,
            'stop_loss_pct': 0.03,  # %3 stop loss
            'take_profit_pct': 0.08,  # %8 take profit
            'max_hold_days': 7,
            'trend_strength_threshold': 0.6
        }
        
        self.min_confidence = 0.6
        
    async def analyze(self, symbol: str, historical_data: List[Dict],
                     current_price: float, **kwargs) -> Optional[Signal]:
        """
        Swing trading analizi
        
        Args:
            symbol: Sembol adı
            historical_data: Geçmiş veri (minimum 50 candle)
            current_price: Güncel fiyat
            **kwargs: Ek veriler
            
        Returns:
            Swing trading sinyali
        """
        if not self.is_active or len(historical_data) < 50:
            return None
            
        try:
            # Data preparation
            closes = [d['close'] for d in historical_data]
            highs = [d['high'] for d in historical_data]
            lows = [d['low'] for d in historical_data]
            volumes = [d['volume'] for d in historical_data]
            
            # Technical indicators
            ema_short = self._calculate_ema(closes, self.parameters['ema_short'])
            ema_long = self._calculate_ema(closes, self.parameters['ema_long'])
            rsi = self._calculate_rsi(closes, period=14)
            macd_line, macd_signal, macd_histogram = self._calculate_macd(closes)
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(closes)
            
            # Trend analysis
            trend_strength = self._analyze_trend_strength(closes, ema_short, ema_long)
            support_resistance = self._find_support_resistance(highs, lows, closes)
            
            # Volume confirmation
            volume_confirmed = self._check_volume_confirmation(volumes) if volumes else True
            
            # Signal generation
            signal = self._generate_swing_signal(
                symbol, current_price, ema_short, ema_long, rsi,
                macd_line, macd_signal, macd_histogram,
                bb_upper, bb_middle, bb_lower,
                trend_strength, support_resistance, volume_confirmed
            )
            
            if signal:
                self.signals_generated += 1
                
            return signal
            
        except Exception as e:
            self.logger.error(f"Error in swing analysis for {symbol}: {str(e)}")
            return None
    
    def _generate_swing_signal(self, symbol: str, price: float,
                             ema_short: float, ema_long: float, rsi: float,
                             macd_line: float, macd_signal: float, macd_hist: float,
                             bb_upper: float, bb_middle: float, bb_lower: float,
                             trend_strength: float, support_resistance: Dict,
                             volume_confirmed: bool) -> Optional[Signal]:
        """Swing trading sinyali oluşturma"""
        
        confidence = 0.0
        signal_type = SignalType.HOLD
        
        # BUY sinyali koşulları
        buy_conditions = [
            ema_short > ema_long,  # Bullish EMA crossover
            macd_line > macd_signal,  # MACD bullish
            macd_hist > 0,  # MACD histogram positive
            rsi < self.parameters['rsi_overbought'],  # RSI not overbought
            price <= bb_lower * 1.02,  # Bollinger alt bandına yakın
            price > support_resistance.get('support', 0),  # Destek üzerinde
            trend_strength > self.parameters['trend_strength_threshold']  # Güçlü trend
        ]
        
        # SELL sinyali koşulları
        sell_conditions = [
            ema_short < ema_long,  # Bearish EMA crossover
            macd_line < macd_signal,  # MACD bearish
            macd_hist < 0,  # MACD histogram negative
            rsi > self.parameters['rsi_oversold'],  # RSI not oversold
            price >= bb_upper * 0.98,  # Bollinger üst bandına yakın
            price < support_resistance.get('resistance', float('inf')),  # Direnç altında
            trend_strength > self.parameters['trend_strength_threshold']  # Güçlü trend
        ]
        
        # Volume confirmation
        if self.parameters['volume_confirmation'] and not volume_confirmed:
            return None
        
        # BUY signal
        buy_score = sum(buy_conditions)
        if buy_score >= 4:
            confidence = min(0.95, 0.4 + (buy_score * 0.08))
            
            # EMA crossover özel bonusu
            if ema_short > ema_long and abs(ema_short - ema_long) / ema_long > 0.01:
                confidence += 0.1
                
            # Bollinger band squeeze bonusu
            if (bb_upper - bb_lower) / bb_middle < 0.05:  # Dar band
                confidence += 0.05
                
            signal_type = SignalType.STRONG_BUY if confidence > 0.8 else SignalType.BUY
        
        # SELL signal
        sell_score = sum(sell_conditions)
        if sell_score >= 4:
            confidence = min(0.95, 0.4 + (sell_score * 0.08))
            
            # EMA crossover özel bonusu
            if ema_short < ema_long and abs(ema_short - ema_long) / ema_long > 0.01:
                confidence += 0.1
                
            # Bollinger band squeeze bonusu
            if (bb_upper - bb_lower) / bb_middle < 0.05:
                confidence += 0.05
                
            signal_type = SignalType.STRONG_SELL if confidence > 0.8 else SignalType.SELL
        
        if signal_type != SignalType.HOLD and confidence >= self.min_confidence:
            signal = Signal(symbol, signal_type, confidence, price)
            
            # Metadata ekleme
            signal.add_metadata('ema_short', ema_short)
            signal.add_metadata('ema_long', ema_long)
            signal.add_metadata('rsi', rsi)
            signal.add_metadata('macd_line', macd_line)
            signal.add_metadata('macd_signal', macd_signal)
            signal.add_metadata('macd_histogram', macd_hist)
            signal.add_metadata('trend_strength', trend_strength)
            signal.add_metadata('support', support_resistance.get('support'))
            signal.add_metadata('resistance', support_resistance.get('resistance'))
            signal.add_metadata('strategy_type', 'swing')
            
            return signal
            
        return None
    
    def get_risk_parameters(self, signal: Signal) -> Dict:
        """
        Swing trading risk parametreleri
        
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
        
        # Position size - trend strength bazlı
        base_position_pct = 0.08  # %8 base position (scalping'den fazla)
        trend_strength = signal.metadata.get('trend_strength', 0.5)
        trend_multiplier = min(1.5, 0.8 + trend_strength)
        position_size_pct = base_position_pct * trend_multiplier
        
        return {
            'stop_loss_price': stop_loss_price,
            'take_profit_price': take_profit_price,
            'position_size_percentage': position_size_pct,
            'max_hold_days': self.parameters['max_hold_days'],
            'risk_reward_ratio': self.parameters['take_profit_pct'] / self.parameters['stop_loss_pct'],
            'entry_type': 'limit',  # Swing için limit order
            'entry_offset_pct': 0.002  # %0.2 offset for better entry
        }
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Exponential Moving Average hesaplama"""
        if len(prices) < period:
            return np.mean(prices) if prices else 0
            
        multiplier = 2 / (period + 1)
        ema = prices[0]  # İlk değer
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
            
        return ema
    
    def _calculate_macd(self, prices: List[float]) -> tuple:
        """MACD hesaplama"""
        if len(prices) < 26:
            return 0, 0, 0
            
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        macd_line = ema_12 - ema_26
        
        # MACD signal line (9-period EMA of MACD line)
        # Basitleştirilmiş hesaplama
        macd_signal = macd_line * 0.8  # Approximation
        
        macd_histogram = macd_line - macd_signal
        
        return macd_line, macd_signal, macd_histogram
    
    def _calculate_bollinger_bands(self, prices: List[float]) -> tuple:
        """Bollinger Bands hesaplama"""
        period = self.parameters['bollinger_period']
        std_dev = self.parameters['bollinger_std']
        
        if len(prices) < period:
            avg = np.mean(prices) if prices else 0
            return avg, avg, avg
            
        recent_prices = prices[-period:]
        sma = np.mean(recent_prices)
        std = np.std(recent_prices)
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return upper_band, sma, lower_band
    
    def _analyze_trend_strength(self, prices: List[float], 
                              ema_short: float, ema_long: float) -> float:
        """Trend gücü analizi"""
        if len(prices) < 20:
            return 0.5
            
        # EMA divergence
        ema_divergence = abs(ema_short - ema_long) / ema_long if ema_long > 0 else 0
        
        # Price momentum
        recent_change = (prices[-1] - prices[-10]) / prices[-10] if len(prices) >= 10 else 0
        
        # Trend consistency (son 10 candle'da kaç tanesi trend yönünde)
        trend_direction = 1 if ema_short > ema_long else -1
        consistent_moves = 0
        
        for i in range(1, min(11, len(prices))):
            move = prices[-i] - prices[-(i+1)]
            if (trend_direction > 0 and move > 0) or (trend_direction < 0 and move < 0):
                consistent_moves += 1
        
        consistency_ratio = consistent_moves / 10
        
        # Trend strength score
        strength = min(1.0, (ema_divergence * 10) + abs(recent_change) + consistency_ratio)
        
        return strength
    
    def _find_support_resistance(self, highs: List[float], lows: List[float],
                               closes: List[float]) -> Dict:
        """Support ve resistance seviyeleri bulma"""
        if len(closes) < 20:
            return {'support': 0, 'resistance': float('inf')}
            
        # Son 20 periyotta pivot noktaları bul
        recent_highs = highs[-20:]
        recent_lows = lows[-20:]
        recent_closes = closes[-20:]
        
        # Resistance: Son 20 periyotun en yüksek değerinin %98'i
        resistance = max(recent_highs) * 0.98
        
        # Support: Son 20 periyotun en düşük değerinin %102'si
        support = min(recent_lows) * 1.02
        
        # Pivot noktaları ile doğrulama
        pivot_points = []
        for i in range(2, len(recent_closes) - 2):
            # Local maximum
            if (recent_closes[i] > recent_closes[i-1] and 
                recent_closes[i] > recent_closes[i+1] and
                recent_closes[i] > recent_closes[i-2] and
                recent_closes[i] > recent_closes[i+2]):
                pivot_points.append(recent_closes[i])
                
            # Local minimum
            elif (recent_closes[i] < recent_closes[i-1] and 
                  recent_closes[i] < recent_closes[i+1] and
                  recent_closes[i] < recent_closes[i-2] and
                  recent_closes[i] < recent_closes[i+2]):
                pivot_points.append(recent_closes[i])
        
        # Pivot noktalarından daha güçlü S/R seviyeleri
        if pivot_points:
            pivot_resistance = max([p for p in pivot_points if p > recent_closes[-1]], 
                                 default=resistance)
            pivot_support = min([p for p in pivot_points if p < recent_closes[-1]], 
                               default=support)
            
            resistance = min(resistance, pivot_resistance)
            support = max(support, pivot_support)
        
        return {
            'support': support,
            'resistance': resistance,
            'pivot_points': pivot_points
        }
    
    def _check_volume_confirmation(self, volumes: List[float]) -> bool:
        """Volume onayı kontrolü"""
        if len(volumes) < 10:
            return True  # Insufficient data, assume OK
            
        avg_volume = np.mean(volumes[-10:-1])  # Son 9 candle ortalaması
        current_volume = volumes[-1]
        
        # Current volume ortalamadan %20 fazla olmalı
        return current_volume > avg_volume * 1.2
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """RSI hesaplama"""
        if len(prices) < period + 1:
            return 50
            
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
    
    def analyze_market_structure(self, historical_data: List[Dict]) -> Dict:
        """
        Market structure analizi
        
        Args:
            historical_data: Geçmiş veri
            
        Returns:
            Market structure bilgileri
        """
        if len(historical_data) < 50:
            return {'structure': 'unknown'}
            
        closes = [d['close'] for d in historical_data]
        highs = [d['high'] for d in historical_data]
        lows = [d['low'] for d in historical_data]
        
        # Higher highs, higher lows (uptrend)
        # Lower highs, lower lows (downtrend)
        
        recent_highs = []
        recent_lows = []
        
        # Son 30 periyotta swing high/low noktaları bul
        for i in range(5, len(closes) - 5):
            # Swing high
            if (highs[i] > max(highs[i-5:i]) and 
                highs[i] > max(highs[i+1:i+6])):
                recent_highs.append((i, highs[i]))
                
            # Swing low
            if (lows[i] < min(lows[i-5:i]) and 
                lows[i] < min(lows[i+1:i+6])):
                recent_lows.append((i, lows[i]))
        
        # Trend structure belirleme
        structure = 'sideways'
        
        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            # Higher highs ve higher lows kontrolü
            hh_count = sum(1 for i in range(1, len(recent_highs)) 
                          if recent_highs[i][1] > recent_highs[i-1][1])
            hl_count = sum(1 for i in range(1, len(recent_lows)) 
                          if recent_lows[i][1] > recent_lows[i-1][1])
            
            # Lower highs ve lower lows kontrolü
            lh_count = sum(1 for i in range(1, len(recent_highs)) 
                          if recent_highs[i][1] < recent_highs[i-1][1])
            ll_count = sum(1 for i in range(1, len(recent_lows)) 
                          if recent_lows[i][1] < recent_lows[i-1][1])
            
            # Uptrend
            if hh_count >= lh_count and hl_count >= ll_count:
                structure = 'uptrend'
            # Downtrend
            elif lh_count > hh_count and ll_count > hl_count:
                structure = 'downtrend'
        
        return {
            'structure': structure,
            'swing_highs': recent_highs[-5:],  # Son 5 swing high
            'swing_lows': recent_lows[-5:],   # Son 5 swing low
            'trend_changes': len(recent_highs) + len(recent_lows)
        }
    
    def calculate_optimal_entry(self, signal: Signal, 
                              support_resistance: Dict) -> Dict:
        """
        Optimal giriş noktası hesaplama
        
        Args:
            signal: Trading sinyali
            support_resistance: Destek/direnç seviyeleri
            
        Returns:
            Optimal entry bilgileri
        """
        current_price = signal.price
        
        if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            # Buy için support seviyesine yakın giriş
            support = support_resistance.get('support', current_price * 0.98)
            optimal_entry = max(support, current_price * 0.995)  # %0.5 tolerance
            
            return {
                'entry_price': optimal_entry,
                'entry_type': 'limit',
                'wait_for_pullback': current_price > optimal_entry * 1.01,
                'max_wait_minutes': 60
            }
            
        else:  # SELL signals
            # Sell için resistance seviyesine yakın giriş
            resistance = support_resistance.get('resistance', current_price * 1.02)
            optimal_entry = min(resistance, current_price * 1.005)  # %0.5 tolerance
            
            return {
                'entry_price': optimal_entry,
                'entry_type': 'limit',
                'wait_for_bounce': current_price < optimal_entry * 0.99,
                'max_wait_minutes': 60
            }
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """EMA hesaplama"""
        if len(prices) < period:
            return np.mean(prices) if prices else 0
            
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
            
        return ema
    
    def get_swing_opportunities(self, symbols_data: Dict[str, Dict]) -> List[Dict]:
        """
        Swing trading fırsatlarını değerlendirme
        
        Args:
            symbols_data: Sembol verileri
            
        Returns:
            Swing fırsatları listesi
        """
        opportunities = []
        
        for symbol, data in symbols_data.items():
            historical_data = data.get('historical_data', [])
            current_price = data.get('current_price', 0)
            
            if len(historical_data) >= 50 and current_price > 0:
                # Market structure analizi
                market_structure = self.analyze_market_structure(historical_data)
                
                # Trend reversal potansiyeli
                reversal_score = self._calculate_reversal_potential(historical_data)
                
                # Volume trend
                volumes = [d['volume'] for d in historical_data if 'volume' in d]
                volume_trend = self._analyze_volume_trend(volumes)
                
                if reversal_score > 0.6:  # Yüksek reversal potansiyeli
                    opportunities.append({
                        'symbol': symbol,
                        'current_price': current_price,
                        'reversal_score': reversal_score,
                        'market_structure': market_structure['structure'],
                        'volume_trend': volume_trend,
                        'opportunity_type': 'trend_reversal',
                        'timeframe': self.timeframe
                    })
        
        # Reversal score'a göre sırala
        opportunities.sort(key=lambda x: x['reversal_score'], reverse=True)
        
        return opportunities[:5]  # En iyi 5 fırsat
    
    def _calculate_reversal_potential(self, historical_data: List[Dict]) -> float:
        """Trend reversal potansiyeli hesaplama"""
        if len(historical_data) < 20:
            return 0
            
        closes = [d['close'] for d in historical_data]
        
        # Son 10 vs önceki 10 periyot karşılaştırması
        recent_avg = np.mean(closes[-10:])
        previous_avg = np.mean(closes[-20:-10])
        
        # RSI divergence
        rsi_recent = self._calculate_rsi(closes[-10:])
        rsi_previous = self._calculate_rsi(closes[-20:-10])
        
        # Price vs RSI divergence
        price_change = (recent_avg - previous_avg) / previous_avg
        rsi_change = (rsi_recent - rsi_previous) / 100
        
        # Divergence score
        divergence_score = abs(price_change - rsi_change)
        
        # Oversold/overbought score
        extremity_score = 0
        if rsi_recent < 30:  # Oversold
            extremity_score = (30 - rsi_recent) / 30
        elif rsi_recent > 70:  # Overbought
            extremity_score = (rsi_recent - 70) / 30
        
        # Combine scores
        reversal_potential = min(1.0, divergence_score + extremity_score)
        
        return reversal_potential
    
    def _analyze_volume_trend(self, volumes: List[float]) -> str:
        """Volume trend analizi"""
        if len(volumes) < 10:
            return 'unknown'
            
        recent_avg = np.mean(volumes[-5:])
        previous_avg = np.mean(volumes[-10:-5])
        
        change_ratio = recent_avg / previous_avg if previous_avg > 0 else 1
        
        if change_ratio > 1.2:
            return 'increasing'
        elif change_ratio < 0.8:
            return 'decreasing'
        else:
            return 'stable'