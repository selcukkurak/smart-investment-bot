"""
Smart Investment Bot - Base Strategy
Abstract base class for trading strategies
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class Signal:
    """Trading signal with confidence and reasoning"""
    
    def __init__(self, signal_type: SignalType, confidence: float,
                 price: float, reasoning: str, indicators: Dict[str, Any]):
        self.signal_type = signal_type
        self.confidence = confidence  # 0.0 to 1.0
        self.price = price
        self.reasoning = reasoning
        self.indicators = indicators
        self.timestamp = datetime.now()


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies
    """
    
    def __init__(self, name: str, timeframes: List[str], 
                 min_confidence: float = 0.6):
        self.name = name
        self.timeframes = timeframes
        self.min_confidence = min_confidence
        self.signals_history: List[Signal] = []
        
    @abstractmethod
    def analyze(self, symbol: str, data: List[Dict]) -> Signal:
        """
        Analyze market data and generate trading signal
        
        Args:
            symbol: Trading symbol
            data: List of OHLCV dictionaries with technical indicators
            
        Returns:
            Signal: Trading signal with confidence and reasoning
        """
        pass
    
    @abstractmethod
    def get_required_indicators(self) -> List[str]:
        """Return list of required technical indicators for this strategy"""
        pass
    
    def validate_data(self, data: List[Dict]) -> bool:
        """Validate that data contains required indicators"""
        if not data or not isinstance(data[0], dict):
            return False
        
        required = self.get_required_indicators()
        return all(indicator in data[-1] for indicator in required)
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[Optional[float]]:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return [None] * len(prices)
        
        rsi = []
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        rsi.append(None)  # First price has no RSI
        
        for i in range(period, len(prices)):
            recent_deltas = deltas[i-period:i]
            gains = [max(d, 0) for d in recent_deltas]
            losses = [abs(min(d, 0)) for d in recent_deltas]
            
            avg_gain = sum(gains) / period
            avg_loss = sum(losses) / period
            
            if avg_loss == 0:
                rsi_value = 100
            else:
                rs = avg_gain / avg_loss
                rsi_value = 100 - (100 / (1 + rs))
            
            rsi.append(rsi_value)
        
        while len(rsi) < len(prices):
            rsi.insert(0, None)
        
        return rsi
    
    def calculate_macd(self, prices: List[float], fast: int = 12, 
                      slow: int = 26, signal: int = 9) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
        """Calculate MACD, Signal line, and Histogram"""
        # Use the technical analysis module for calculations
        from ..analysis.technical_analysis import TechnicalAnalysis
        return TechnicalAnalysis.calculate_macd(prices, fast, slow, signal)
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, 
                                std_dev: int = 2) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
        """Calculate Bollinger Bands"""
        from ..analysis.technical_analysis import TechnicalAnalysis
        return TechnicalAnalysis.calculate_bollinger_bands(prices, period, std_dev)
    
    def add_technical_indicators(self, data: List[Dict]) -> List[Dict]:
        """Add common technical indicators to data"""
        if not data:
            return data
        
        # Extract prices for calculations
        prices = [d.get('close', d.get('price', 0)) for d in data]
        volumes = [d.get('volume', 0) for d in data]
        
        # Calculate indicators
        from ..analysis.technical_analysis import TechnicalAnalysis
        sma_20 = TechnicalAnalysis.calculate_sma(prices, 20)
        sma_50 = TechnicalAnalysis.calculate_sma(prices, 50)
        ema_12 = TechnicalAnalysis.calculate_ema(prices, 12)
        ema_26 = TechnicalAnalysis.calculate_ema(prices, 26)
        rsi = TechnicalAnalysis.calculate_rsi(prices)
        macd, signal_line, histogram = TechnicalAnalysis.calculate_macd(prices)
        bb_upper, bb_middle, bb_lower = TechnicalAnalysis.calculate_bollinger_bands(prices)
        
        # Add indicators to data
        enhanced_data = []
        for i, d in enumerate(data):
            enhanced = d.copy()
            enhanced.update({
                'SMA_20': sma_20[i] if i < len(sma_20) else None,
                'SMA_50': sma_50[i] if i < len(sma_50) else None,
                'EMA_12': ema_12[i] if i < len(ema_12) else None,
                'EMA_26': ema_26[i] if i < len(ema_26) else None,
                'RSI': rsi[i] if i < len(rsi) else None,
                'MACD': macd[i] if i < len(macd) else None,
                'MACD_Signal': signal_line[i] if i < len(signal_line) else None,
                'MACD_Histogram': histogram[i] if i < len(histogram) else None,
                'BB_Upper': bb_upper[i] if i < len(bb_upper) else None,
                'BB_Middle': bb_middle[i] if i < len(bb_middle) else None,
                'BB_Lower': bb_lower[i] if i < len(bb_lower) else None,
            })
            
            # Volume indicators
            if i >= 20:
                avg_volume = sum(volumes[i-19:i+1]) / 20
                enhanced['Volume_SMA'] = avg_volume
                enhanced['Volume_Ratio'] = volumes[i] / avg_volume if avg_volume > 0 else 1
            else:
                enhanced['Volume_SMA'] = None
                enhanced['Volume_Ratio'] = 1
            
            enhanced_data.append(enhanced)
        
        return enhanced_data
    
    def record_signal(self, signal: Signal):
        """Record a signal in history"""
        self.signals_history.append(signal)
        
        # Keep only last 1000 signals to manage memory
        if len(self.signals_history) > 1000:
            self.signals_history = self.signals_history[-1000:]
    
    def get_recent_signals(self, limit: int = 10) -> List[Signal]:
        """Get recent signals"""
        return self.signals_history[-limit:]
    
    def get_signal_performance(self, days: int = 30) -> Dict[str, Any]:
        """Analyze strategy performance over recent signals"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_signals = [
            s for s in self.signals_history 
            if s.timestamp >= cutoff_date
        ]
        
        if not recent_signals:
            return {'total_signals': 0}
        
        buy_signals = [s for s in recent_signals if s.signal_type == SignalType.BUY]
        sell_signals = [s for s in recent_signals if s.signal_type == SignalType.SELL]
        
        avg_confidence = sum(s.confidence for s in recent_signals) / len(recent_signals)
        
        return {
            'total_signals': len(recent_signals),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'avg_confidence': avg_confidence,
            'strategy_name': self.name,
            'period_days': days
        }