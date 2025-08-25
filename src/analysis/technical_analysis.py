"""
Technical Analysis - RSI, MACD, Bollinger Bands ve diğer indikatörler
Teknik analiz araçları ve hesaplama fonksiyonları
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging


class TechnicalAnalysis:
    """
    Teknik analiz sınıfı
    
    Desteklenen indikatörler:
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - Bollinger Bands
    - Moving Averages (SMA, EMA)
    - Stochastic Oscillator
    - Average True Range (ATR)
    - Volume indicators
    """
    
    def __init__(self):
        self.logger = logging.getLogger('TechnicalAnalysis')
        
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """
        RSI hesaplama
        
        Args:
            prices: Fiyat listesi
            period: RSI periyodu
            
        Returns:
            RSI değerleri listesi
        """
        if len(prices) < period + 1:
            return [50.0] * len(prices)
            
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        rsi_values = []
        
        # İlk RSI değeri
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
        
        # Smoothed RSI hesaplama
        for i in range(period, len(deltas)):
            gain = gains[i]
            loss = losses[i]
            
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
            
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                rsi_values.append(rsi)
        
        # Başlangıç değerleri için padding
        result = [50.0] * period + rsi_values
        
        return result[:len(prices)]
    
    def calculate_macd(self, prices: List[float], fast_period: int = 12,
                      slow_period: int = 26, signal_period: int = 9) -> Tuple[List[float], List[float], List[float]]:
        """
        MACD hesaplama
        
        Args:
            prices: Fiyat listesi
            fast_period: Hızlı EMA periyodu
            slow_period: Yavaş EMA periyodu
            signal_period: Signal line periyodu
            
        Returns:
            (MACD line, Signal line, Histogram)
        """
        if len(prices) < slow_period:
            zeros = [0.0] * len(prices)
            return zeros, zeros, zeros
            
        # EMA hesaplama
        ema_fast = self.calculate_ema(prices, fast_period)
        ema_slow = self.calculate_ema(prices, slow_period)
        
        # MACD line
        macd_line = [fast - slow for fast, slow in zip(ema_fast, ema_slow)]
        
        # Signal line (MACD'nin EMA'sı)
        signal_line = self.calculate_ema(macd_line, signal_period)
        
        # MACD histogram
        histogram = [macd - signal for macd, signal in zip(macd_line, signal_line)]
        
        return macd_line, signal_line, histogram
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20,
                                std_dev: float = 2.0) -> Tuple[List[float], List[float], List[float]]:
        """
        Bollinger Bands hesaplama
        
        Args:
            prices: Fiyat listesi
            period: Moving average periyodu
            std_dev: Standart sapma çarpanı
            
        Returns:
            (Upper band, Middle band/SMA, Lower band)
        """
        if len(prices) < period:
            avg = np.mean(prices) if prices else 0
            return [avg] * len(prices), [avg] * len(prices), [avg] * len(prices)
            
        sma = self.calculate_sma(prices, period)
        
        upper_band = []
        lower_band = []
        
        for i in range(len(prices)):
            if i < period - 1:
                # Insufficient data
                upper_band.append(sma[i])
                lower_band.append(sma[i])
            else:
                # Calculate standard deviation for the period
                period_prices = prices[i - period + 1:i + 1]
                std = np.std(period_prices)
                
                upper_band.append(sma[i] + (std * std_dev))
                lower_band.append(sma[i] - (std * std_dev))
        
        return upper_band, sma, lower_band
    
    def calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """
        Simple Moving Average hesaplama
        
        Args:
            prices: Fiyat listesi
            period: Periyot
            
        Returns:
            SMA değerleri
        """
        if len(prices) < period:
            return prices.copy()
            
        sma_values = []
        
        for i in range(len(prices)):
            if i < period - 1:
                # İlk değerler için mevcut fiyatı kullan
                sma_values.append(prices[i])
            else:
                period_prices = prices[i - period + 1:i + 1]
                sma_values.append(np.mean(period_prices))
        
        return sma_values
    
    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """
        Exponential Moving Average hesaplama
        
        Args:
            prices: Fiyat listesi
            period: Periyot
            
        Returns:
            EMA değerleri
        """
        if not prices:
            return []
            
        multiplier = 2.0 / (period + 1)
        ema_values = [prices[0]]  # İlk değer
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values
    
    def calculate_stochastic(self, highs: List[float], lows: List[float],
                           closes: List[float], k_period: int = 14,
                           d_period: int = 3) -> Tuple[List[float], List[float]]:
        """
        Stochastic Oscillator hesaplama
        
        Args:
            highs: Yüksek fiyatlar
            lows: Düşük fiyatlar
            closes: Kapanış fiyatları
            k_period: %K periyodu
            d_period: %D periyodu
            
        Returns:
            (%K values, %D values)
        """
        if len(closes) < k_period:
            return [50.0] * len(closes), [50.0] * len(closes)
            
        k_values = []
        
        for i in range(len(closes)):
            if i < k_period - 1:
                k_values.append(50.0)
            else:
                period_highs = highs[i - k_period + 1:i + 1]
                period_lows = lows[i - k_period + 1:i + 1]
                
                highest_high = max(period_highs)
                lowest_low = min(period_lows)
                
                if highest_high == lowest_low:
                    k_values.append(50.0)
                else:
                    k_percent = ((closes[i] - lowest_low) / (highest_high - lowest_low)) * 100
                    k_values.append(k_percent)
        
        # %D hesaplama (%K'nın SMA'sı)
        d_values = self.calculate_sma(k_values, d_period)
        
        return k_values, d_values
    
    def calculate_atr(self, highs: List[float], lows: List[float],
                     closes: List[float], period: int = 14) -> List[float]:
        """
        Average True Range hesaplama
        
        Args:
            highs: Yüksek fiyatlar
            lows: Düşük fiyatlar
            closes: Kapanış fiyatları
            period: ATR periyodu
            
        Returns:
            ATR değerleri
        """
        if len(closes) < 2:
            return [0.0] * len(closes)
            
        true_ranges = []
        
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_close_prev = abs(highs[i] - closes[i-1])
            low_close_prev = abs(lows[i] - closes[i-1])
            
            true_range = max(high_low, high_close_prev, low_close_prev)
            true_ranges.append(true_range)
        
        # İlk değer için padding
        true_ranges.insert(0, highs[0] - lows[0])
        
        # ATR hesaplama (True Range'in SMA'sı)
        atr_values = self.calculate_sma(true_ranges, period)
        
        return atr_values
    
    def calculate_volume_indicators(self, prices: List[float], 
                                  volumes: List[float]) -> Dict[str, List[float]]:
        """
        Volume indikatörleri hesaplama
        
        Args:
            prices: Fiyat listesi
            volumes: Volume listesi
            
        Returns:
            Volume indikatörleri
        """
        if len(prices) != len(volumes) or len(prices) < 20:
            return {
                'volume_sma': volumes.copy() if volumes else [],
                'vwap': prices.copy() if prices else [],
                'obv': [0.0] * len(prices)
            }
        
        # Volume SMA
        volume_sma = self.calculate_sma(volumes, 20)
        
        # VWAP (Volume Weighted Average Price)
        vwap = self._calculate_vwap(prices, volumes)
        
        # OBV (On Balance Volume)
        obv = self._calculate_obv(prices, volumes)
        
        return {
            'volume_sma': volume_sma,
            'vwap': vwap,
            'obv': obv
        }
    
    def _calculate_vwap(self, prices: List[float], volumes: List[float]) -> List[float]:
        """VWAP hesaplama"""
        vwap_values = []
        cumulative_pv = 0
        cumulative_volume = 0
        
        for price, volume in zip(prices, volumes):
            cumulative_pv += price * volume
            cumulative_volume += volume
            
            if cumulative_volume > 0:
                vwap = cumulative_pv / cumulative_volume
            else:
                vwap = price
                
            vwap_values.append(vwap)
        
        return vwap_values
    
    def _calculate_obv(self, prices: List[float], volumes: List[float]) -> List[float]:
        """On Balance Volume hesaplama"""
        if len(prices) < 2:
            return [0.0] * len(prices)
            
        obv_values = [0.0]  # İlk değer 0
        
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                obv = obv_values[-1] + volumes[i]
            elif prices[i] < prices[i-1]:
                obv = obv_values[-1] - volumes[i]
            else:
                obv = obv_values[-1]
                
            obv_values.append(obv)
        
        return obv_values
    
    def identify_patterns(self, highs: List[float], lows: List[float],
                         closes: List[float]) -> Dict[str, bool]:
        """
        Chart pattern tanıma
        
        Args:
            highs: Yüksek fiyatlar
            lows: Düşük fiyatlar
            closes: Kapanış fiyatları
            
        Returns:
            Tanınan pattern'lar
        """
        patterns = {
            'double_top': False,
            'double_bottom': False,
            'head_shoulders': False,
            'triangle': False,
            'flag': False,
            'wedge': False
        }
        
        if len(closes) < 20:
            return patterns
            
        # Double Top/Bottom detection
        patterns.update(self._detect_double_patterns(highs, lows, closes))
        
        # Triangle pattern detection
        patterns['triangle'] = self._detect_triangle_pattern(highs, lows)
        
        # Flag pattern detection
        patterns['flag'] = self._detect_flag_pattern(closes)
        
        return patterns
    
    def _detect_double_patterns(self, highs: List[float], lows: List[float],
                              closes: List[float]) -> Dict[str, bool]:
        """Double Top/Bottom pattern detection"""
        patterns = {'double_top': False, 'double_bottom': False}
        
        if len(closes) < 20:
            return patterns
            
        # Son 20 periyotta swing high/low bul
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(closes) - 2):
            # Swing high
            if (highs[i] > highs[i-1] and highs[i] > highs[i+1] and
                highs[i] > highs[i-2] and highs[i] > highs[i+2]):
                swing_highs.append((i, highs[i]))
                
            # Swing low
            if (lows[i] < lows[i-1] and lows[i] < lows[i+1] and
                lows[i] < lows[i-2] and lows[i] < lows[i+2]):
                swing_lows.append((i, lows[i]))
        
        # Double Top check
        if len(swing_highs) >= 2:
            last_two_highs = swing_highs[-2:]
            high1_idx, high1_price = last_two_highs[0]
            high2_idx, high2_price = last_two_highs[1]
            
            # İki tepe birbirine yakın mı (%2 tolerance)
            if abs(high1_price - high2_price) / high1_price < 0.02:
                # Arada düşüş var mı
                between_lows = [lows[i] for i in range(high1_idx, high2_idx + 1)]
                if min(between_lows) < high1_price * 0.95:
                    patterns['double_top'] = True
        
        # Double Bottom check
        if len(swing_lows) >= 2:
            last_two_lows = swing_lows[-2:]
            low1_idx, low1_price = last_two_lows[0]
            low2_idx, low2_price = last_two_lows[1]
            
            # İki dip birbirine yakın mı
            if abs(low1_price - low2_price) / low1_price < 0.02:
                # Arada yükseliş var mı
                between_highs = [highs[i] for i in range(low1_idx, low2_idx + 1)]
                if max(between_highs) > low1_price * 1.05:
                    patterns['double_bottom'] = True
        
        return patterns
    
    def _detect_triangle_pattern(self, highs: List[float], lows: List[float]) -> bool:
        """Triangle pattern detection"""
        if len(highs) < 20:
            return False
            
        # Son 20 periyotta trend line eğimleri
        recent_highs = highs[-20:]
        recent_lows = lows[-20:]
        
        # Linear regression for trend lines
        x = np.arange(len(recent_highs))
        
        # High trend line eğimi
        high_slope = np.polyfit(x, recent_highs, 1)[0]
        
        # Low trend line eğimi
        low_slope = np.polyfit(x, recent_lows, 1)[0]
        
        # Converging lines (triangle)
        # High trend line düşüyor, low trend line yükseliyor
        return high_slope < -0.001 and low_slope > 0.001
    
    def _detect_flag_pattern(self, closes: List[float]) -> bool:
        """Flag pattern detection"""
        if len(closes) < 15:
            return False
            
        # Flag: Güçlü trend + consolidation
        
        # Son 15 candle'ı analiz et
        recent_closes = closes[-15:]
        
        # İlk 5 candle trend kontrolü
        trend_start = recent_closes[:5]
        trend_change = (trend_start[-1] - trend_start[0]) / trend_start[0]
        
        # Güçlü trend var mı (%3'ten fazla)
        if abs(trend_change) < 0.03:
            return False
            
        # Son 10 candle consolidation kontrolü
        consolidation = recent_closes[-10:]
        consolidation_range = (max(consolidation) - min(consolidation)) / np.mean(consolidation)
        
        # Dar range consolidation (%2'den az)
        return consolidation_range < 0.02
    
    def calculate_support_resistance(self, highs: List[float], lows: List[float],
                                   closes: List[float], lookback: int = 50) -> Dict:
        """
        Support ve Resistance seviyeler hesaplama
        
        Args:
            highs: Yüksek fiyatlar
            lows: Düşük fiyatlar
            closes: Kapanış fiyatları
            lookback: Geriye bakış periyodu
            
        Returns:
            Support/Resistance seviyeler
        """
        if len(closes) < lookback:
            current_price = closes[-1] if closes else 0
            return {
                'support_levels': [current_price * 0.98],
                'resistance_levels': [current_price * 1.02],
                'current_price': current_price
            }
        
        recent_data = closes[-lookback:]
        recent_highs = highs[-lookback:]
        recent_lows = lows[-lookback:]
        
        # Pivot points bulma
        pivot_highs = []
        pivot_lows = []
        
        for i in range(2, len(recent_data) - 2):
            # Pivot high
            if (recent_highs[i] > recent_highs[i-1] and 
                recent_highs[i] > recent_highs[i+1] and
                recent_highs[i] > recent_highs[i-2] and 
                recent_highs[i] > recent_highs[i+2]):
                pivot_highs.append(recent_highs[i])
                
            # Pivot low
            if (recent_lows[i] < recent_lows[i-1] and 
                recent_lows[i] < recent_lows[i+1] and
                recent_lows[i] < recent_lows[i-2] and 
                recent_lows[i] < recent_lows[i+2]):
                pivot_lows.append(recent_lows[i])
        
        # Support levels (pivot lows + psychological levels)
        support_levels = sorted(set(pivot_lows))[-3:]  # Son 3 support
        
        # Resistance levels (pivot highs + psychological levels)
        resistance_levels = sorted(set(pivot_highs))[-3:]  # Son 3 resistance
        
        # Psychological levels ekleme (round numbers)
        current_price = closes[-1]
        psychological_levels = self._get_psychological_levels(current_price)
        
        support_levels.extend([level for level in psychological_levels if level < current_price])
        resistance_levels.extend([level for level in psychological_levels if level > current_price])
        
        return {
            'support_levels': sorted(support_levels)[-3:],  # En yakın 3 support
            'resistance_levels': sorted(resistance_levels)[:3],  # En yakın 3 resistance
            'current_price': current_price,
            'pivot_highs': pivot_highs,
            'pivot_lows': pivot_lows
        }
    
    def _get_psychological_levels(self, price: float) -> List[float]:
        """Psychological levels (round numbers)"""
        levels = []
        
        # Price magnitude'a göre round numbers
        if price >= 1000:
            # 1000'lik levels
            base = int(price / 1000) * 1000
            levels.extend([base - 1000, base, base + 1000])
        elif price >= 100:
            # 100'lük levels
            base = int(price / 100) * 100
            levels.extend([base - 100, base, base + 100])
        elif price >= 10:
            # 10'luk levels
            base = int(price / 10) * 10
            levels.extend([base - 10, base, base + 10])
        else:
            # 1'lik levels
            base = int(price)
            levels.extend([base - 1, base, base + 1])
        
        return [level for level in levels if level > 0]
    
    def calculate_divergence(self, prices: List[float], indicator_values: List[float],
                           lookback: int = 20) -> Dict:
        """
        Price ve indikatör divergence analizi
        
        Args:
            prices: Fiyat listesi
            indicator_values: İndikatör değerleri (RSI, MACD, etc.)
            lookback: Analiz periyodu
            
        Returns:
            Divergence bilgileri
        """
        if len(prices) < lookback or len(indicator_values) < lookback:
            return {
                'bullish_divergence': False,
                'bearish_divergence': False,
                'divergence_strength': 0
            }
        
        recent_prices = prices[-lookback:]
        recent_indicators = indicator_values[-lookback:]
        
        # Price trend (linear regression slope)
        x = np.arange(len(recent_prices))
        price_slope = np.polyfit(x, recent_prices, 1)[0]
        indicator_slope = np.polyfit(x, recent_indicators, 1)[0]
        
        # Divergence detection
        # Bullish divergence: Price düşüyor, indikatör yükseliyor
        bullish_divergence = price_slope < 0 and indicator_slope > 0
        
        # Bearish divergence: Price yükseliyor, indikatör düşüyor
        bearish_divergence = price_slope > 0 and indicator_slope < 0
        
        # Divergence strength
        if bullish_divergence or bearish_divergence:
            strength = abs(price_slope) + abs(indicator_slope)
        else:
            strength = 0
        
        return {
            'bullish_divergence': bullish_divergence,
            'bearish_divergence': bearish_divergence,
            'divergence_strength': min(1.0, strength * 1000),
            'price_slope': price_slope,
            'indicator_slope': indicator_slope
        }
    
    def analyze_market_structure(self, historical_data: List[Dict]) -> Dict:
        """
        Genel market structure analizi
        
        Args:
            historical_data: Geçmiş veri
            
        Returns:
            Market structure bilgileri
        """
        if len(historical_data) < 50:
            return {
                'trend': 'unknown',
                'strength': 0,
                'phase': 'unknown'
            }
        
        closes = [d['close'] for d in historical_data]
        highs = [d['high'] for d in historical_data]
        lows = [d['low'] for d in historical_data]
        volumes = [d.get('volume', 0) for d in historical_data]
        
        # Moving averages
        sma_20 = self.calculate_sma(closes, 20)
        sma_50 = self.calculate_sma(closes, 50)
        ema_12 = self.calculate_ema(closes, 12)
        ema_26 = self.calculate_ema(closes, 26)
        
        # Trend belirleme
        current_price = closes[-1]
        
        trend = 'sideways'
        if current_price > sma_20[-1] > sma_50[-1] and ema_12[-1] > ema_26[-1]:
            trend = 'uptrend'
        elif current_price < sma_20[-1] < sma_50[-1] and ema_12[-1] < ema_26[-1]:
            trend = 'downtrend'
        
        # Trend strength
        strength = abs(ema_12[-1] - ema_26[-1]) / ema_26[-1] if ema_26[-1] > 0 else 0
        
        # Market phase
        volatility = np.std(closes[-20:]) / np.mean(closes[-20:])
        
        if volatility > 0.03:
            phase = 'volatile'
        elif volatility < 0.01:
            phase = 'consolidation'
        else:
            phase = 'normal'
        
        # Volume analysis
        avg_volume = np.mean(volumes[-20:]) if volumes else 0
        volume_trend = 'increasing' if volumes[-1] > avg_volume * 1.2 else 'normal'
        
        return {
            'trend': trend,
            'strength': min(1.0, strength * 10),
            'phase': phase,
            'volatility': volatility,
            'volume_trend': volume_trend,
            'sma_20': sma_20[-1],
            'sma_50': sma_50[-1],
            'ema_12': ema_12[-1],
            'ema_26': ema_26[-1]
        }
    
    def generate_technical_summary(self, symbol: str, 
                                 historical_data: List[Dict]) -> Dict:
        """
        Kapsamlı teknik analiz özeti
        
        Args:
            symbol: Sembol adı
            historical_data: Geçmiş veri
            
        Returns:
            Teknik analiz özeti
        """
        if len(historical_data) < 50:
            return {
                'symbol': symbol,
                'status': 'insufficient_data',
                'recommendation': 'HOLD'
            }
        
        closes = [d['close'] for d in historical_data]
        highs = [d['high'] for d in historical_data]
        lows = [d['low'] for d in historical_data]
        volumes = [d.get('volume', 0) for d in historical_data]
        
        # Tüm indikatörleri hesapla
        rsi = self.calculate_rsi(closes)[-1]
        macd_line, macd_signal, macd_hist = self.calculate_macd(closes)
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(closes)
        stoch_k, stoch_d = self.calculate_stochastic(highs, lows, closes)
        atr = self.calculate_atr(highs, lows, closes)
        
        # Market structure
        market_structure = self.analyze_market_structure(historical_data)
        
        # Support/Resistance
        sr_levels = self.calculate_support_resistance(highs, lows, closes)
        
        # Pattern recognition
        patterns = self.identify_patterns(highs, lows, closes)
        
        # Overall recommendation
        bullish_signals = [
            rsi[-1] < 40,  # Oversold
            macd_line[-1] > macd_signal[-1],  # MACD bullish
            closes[-1] < bb_lower[-1] * 1.02,  # Near lower BB
            stoch_k[-1] < 30,  # Stochastic oversold
            market_structure['trend'] == 'uptrend'
        ]
        
        bearish_signals = [
            rsi[-1] > 60,  # Overbought
            macd_line[-1] < macd_signal[-1],  # MACD bearish
            closes[-1] > bb_upper[-1] * 0.98,  # Near upper BB
            stoch_k[-1] > 70,  # Stochastic overbought
            market_structure['trend'] == 'downtrend'
        ]
        
        bullish_score = sum(bullish_signals)
        bearish_score = sum(bearish_signals)
        
        if bullish_score >= 3:
            recommendation = 'BUY'
        elif bearish_score >= 3:
            recommendation = 'SELL'
        else:
            recommendation = 'HOLD'
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'current_price': closes[-1],
            'recommendation': recommendation,
            'confidence': max(bullish_score, bearish_score) / 5,
            'indicators': {
                'rsi': rsi[-1],
                'macd_line': macd_line[-1],
                'macd_signal': macd_signal[-1],
                'macd_histogram': macd_hist[-1],
                'bb_upper': bb_upper[-1],
                'bb_middle': bb_middle[-1],
                'bb_lower': bb_lower[-1],
                'stoch_k': stoch_k[-1],
                'stoch_d': stoch_d[-1],
                'atr': atr[-1]
            },
            'market_structure': market_structure,
            'support_resistance': sr_levels,
            'patterns': patterns,
            'bullish_signals': bullish_score,
            'bearish_signals': bearish_score
        }