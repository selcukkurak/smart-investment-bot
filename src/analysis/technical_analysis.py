"""
Smart Investment Bot - Technical Analysis Module
Provides technical indicators and market analysis
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import math


class TechnicalAnalysis:
    """
    Technical analysis tools using only standard library
    """
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> List[Optional[float]]:
        """Calculate Simple Moving Average"""
        sma = []
        for i in range(len(prices)):
            if i < period - 1:
                sma.append(None)
            else:
                avg = sum(prices[i-period+1:i+1]) / period
                sma.append(avg)
        return sma
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[Optional[float]]:
        """Calculate Exponential Moving Average"""
        if not prices or period <= 0:
            return []
        
        ema = []
        multiplier = 2 / (period + 1)
        
        # First EMA is just the first price
        ema.append(prices[0])
        
        for i in range(1, len(prices)):
            ema_value = (prices[i] * multiplier) + (ema[i-1] * (1 - multiplier))
            ema.append(ema_value)
        
        return ema
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return [None] * len(prices)
        
        rsi = []
        
        # Calculate price changes
        deltas = []
        for i in range(1, len(prices)):
            deltas.append(prices[i] - prices[i-1])
        
        # Separate gains and losses
        gains = [max(delta, 0) for delta in deltas]
        losses = [abs(min(delta, 0)) for delta in deltas]
        
        rsi.append(None)  # First price has no RSI
        
        for i in range(period, len(prices)):
            # Calculate average gain and loss over period
            avg_gain = sum(gains[i-period:i]) / period
            avg_loss = sum(losses[i-period:i]) / period
            
            if avg_loss == 0:
                rsi_value = 100
            else:
                rs = avg_gain / avg_loss
                rsi_value = 100 - (100 / (1 + rs))
            
            rsi.append(rsi_value)
        
        # Fill the beginning with None values
        while len(rsi) < len(prices):
            rsi.insert(0, None)
        
        return rsi
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, 
                      signal: int = 9) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
        """Calculate MACD, Signal line, and Histogram"""
        if len(prices) < slow:
            return [None] * len(prices), [None] * len(prices), [None] * len(prices)
        
        # Calculate EMAs
        ema_fast = TechnicalAnalysis.calculate_ema(prices, fast)
        ema_slow = TechnicalAnalysis.calculate_ema(prices, slow)
        
        # Calculate MACD line
        macd = []
        for i in range(len(prices)):
            if ema_fast[i] is not None and ema_slow[i] is not None:
                macd.append(ema_fast[i] - ema_slow[i])
            else:
                macd.append(None)
        
        # Calculate Signal line (EMA of MACD)
        macd_values = [m for m in macd if m is not None]
        if len(macd_values) >= signal:
            signal_ema = TechnicalAnalysis.calculate_ema(macd_values, signal)
            
            # Align signal line with MACD
            signal_line = [None] * len(macd)
            signal_start = len(macd) - len(signal_ema)
            for i, val in enumerate(signal_ema):
                if signal_start + i < len(signal_line):
                    signal_line[signal_start + i] = val
        else:
            signal_line = [None] * len(macd)
        
        # Calculate Histogram
        histogram = []
        for i in range(len(macd)):
            if macd[i] is not None and signal_line[i] is not None:
                histogram.append(macd[i] - signal_line[i])
            else:
                histogram.append(None)
        
        return macd, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, 
                                std_multiplier: float = 2.0) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return [None] * len(prices), [None] * len(prices), [None] * len(prices)
        
        sma = TechnicalAnalysis.calculate_sma(prices, period)
        upper_band = []
        lower_band = []
        
        for i in range(len(prices)):
            if i < period - 1:
                upper_band.append(None)
                lower_band.append(None)
            else:
                # Calculate standard deviation
                period_prices = prices[i-period+1:i+1]
                mean = sma[i]
                variance = sum((p - mean) ** 2 for p in period_prices) / period
                std_dev = math.sqrt(variance)
                
                upper_band.append(mean + (std_dev * std_multiplier))
                lower_band.append(mean - (std_dev * std_multiplier))
        
        return upper_band, sma, lower_band
    
    @staticmethod
    def calculate_volatility(prices: List[float], period: int = 20) -> Optional[float]:
        """Calculate price volatility (standard deviation of returns)"""
        if len(prices) < period + 1:
            return None
        
        # Calculate returns
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        if len(returns) < period:
            return None
        
        # Calculate standard deviation of recent returns
        recent_returns = returns[-period:]
        mean_return = sum(recent_returns) / len(recent_returns)
        variance = sum((r - mean_return) ** 2 for r in recent_returns) / len(recent_returns)
        volatility = math.sqrt(variance)
        
        return volatility
    
    @staticmethod
    def analyze_trend(prices: List[float], short_period: int = 10, 
                     long_period: int = 30) -> Dict[str, Any]:
        """Analyze price trend using moving averages"""
        if len(prices) < long_period:
            return {'trend': 'insufficient_data', 'strength': 0}
        
        short_sma = TechnicalAnalysis.calculate_sma(prices, short_period)
        long_sma = TechnicalAnalysis.calculate_sma(prices, long_period)
        
        current_short = short_sma[-1]
        current_long = long_sma[-1]
        
        if current_short is None or current_long is None:
            return {'trend': 'insufficient_data', 'strength': 0}
        
        # Determine trend direction
        if current_short > current_long:
            trend = 'bullish'
            strength = (current_short - current_long) / current_long
        elif current_short < current_long:
            trend = 'bearish'
            strength = (current_long - current_short) / current_long
        else:
            trend = 'neutral'
            strength = 0
        
        return {
            'trend': trend,
            'strength': abs(strength),
            'short_sma': current_short,
            'long_sma': current_long,
            'difference_percent': strength * 100
        }
    
    @staticmethod
    def calculate_support_resistance(prices: List[float], 
                                   period: int = 20) -> Dict[str, Optional[float]]:
        """Calculate support and resistance levels"""
        if len(prices) < period:
            return {'support': None, 'resistance': None}
        
        recent_prices = prices[-period:]
        
        # Simple support/resistance calculation
        support = min(recent_prices)
        resistance = max(recent_prices)
        current_price = prices[-1]
        
        # Calculate levels as percentages
        support_distance = ((current_price - support) / current_price) * 100
        resistance_distance = ((resistance - current_price) / current_price) * 100
        
        return {
            'support': support,
            'resistance': resistance,
            'current_price': current_price,
            'support_distance_percent': support_distance,
            'resistance_distance_percent': resistance_distance
        }
    
    @staticmethod
    def get_trading_signals(prices: List[float], volumes: List[float] = None) -> Dict[str, Any]:
        """
        Comprehensive technical analysis to generate trading signals
        """
        if len(prices) < 50:
            return {'signal': 'hold', 'confidence': 0, 'reasoning': 'Insufficient data'}
        
        signals = []
        confidence_factors = []
        
        # RSI Analysis
        rsi = TechnicalAnalysis.calculate_rsi(prices)
        current_rsi = rsi[-1] if rsi[-1] is not None else 50
        
        if current_rsi < 30:
            signals.append('buy')
            confidence_factors.append(0.3)
        elif current_rsi > 70:
            signals.append('sell')
            confidence_factors.append(0.3)
        
        # MACD Analysis
        macd, signal_line, histogram = TechnicalAnalysis.calculate_macd(prices)
        if macd[-1] is not None and signal_line[-1] is not None:
            if macd[-1] > signal_line[-1]:
                signals.append('buy')
                confidence_factors.append(0.25)
            else:
                signals.append('sell')
                confidence_factors.append(0.25)
        
        # Trend Analysis
        trend_analysis = TechnicalAnalysis.analyze_trend(prices)
        if trend_analysis['trend'] == 'bullish' and trend_analysis['strength'] > 0.01:
            signals.append('buy')
            confidence_factors.append(0.2)
        elif trend_analysis['trend'] == 'bearish' and trend_analysis['strength'] > 0.01:
            signals.append('sell')
            confidence_factors.append(0.2)
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = TechnicalAnalysis.calculate_bollinger_bands(prices)
        current_price = prices[-1]
        
        if bb_lower[-1] is not None and current_price <= bb_lower[-1]:
            signals.append('buy')
            confidence_factors.append(0.15)
        elif bb_upper[-1] is not None and current_price >= bb_upper[-1]:
            signals.append('sell')
            confidence_factors.append(0.15)
        
        # Volume confirmation
        if volumes and len(volumes) == len(prices):
            avg_volume = sum(volumes[-20:]) / 20
            current_volume = volumes[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            if volume_ratio > 1.5:  # High volume
                confidence_factors.append(0.1)
        
        # Determine final signal
        buy_count = signals.count('buy')
        sell_count = signals.count('sell')
        
        if buy_count > sell_count:
            final_signal = 'buy'
            confidence = min(sum(confidence_factors), 1.0)
        elif sell_count > buy_count:
            final_signal = 'sell'
            confidence = min(sum(confidence_factors), 1.0)
        else:
            final_signal = 'hold'
            confidence = 0.0
        
        reasoning_parts = []
        if current_rsi < 30:
            reasoning_parts.append(f"RSI oversold ({current_rsi:.1f})")
        elif current_rsi > 70:
            reasoning_parts.append(f"RSI overbought ({current_rsi:.1f})")
        
        if trend_analysis['trend'] != 'neutral':
            reasoning_parts.append(f"{trend_analysis['trend']} trend")
        
        reasoning = ', '.join(reasoning_parts) if reasoning_parts else 'No clear signals'
        
        return {
            'signal': final_signal,
            'confidence': confidence,
            'reasoning': reasoning,
            'indicators': {
                'rsi': current_rsi,
                'macd': macd[-1] if macd[-1] is not None else 0,
                'signal_line': signal_line[-1] if signal_line[-1] is not None else 0,
                'bb_upper': bb_upper[-1],
                'bb_middle': bb_middle[-1],
                'bb_lower': bb_lower[-1],
                'trend': trend_analysis['trend'],
                'trend_strength': trend_analysis['strength']
            },
            'timestamp': datetime.now()
        }