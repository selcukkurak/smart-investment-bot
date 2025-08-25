"""
Smart Investment Bot - Base Strategy
Abstract base class for trading strategies
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import pandas as pd


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
    def analyze(self, symbol: str, data: pd.DataFrame) -> Signal:
        """
        Analyze market data and generate trading signal
        
        Args:
            symbol: Trading symbol
            data: OHLCV data with technical indicators
            
        Returns:
            Signal: Trading signal with confidence and reasoning
        """
        pass
    
    @abstractmethod
    def get_required_indicators(self) -> List[str]:
        """Return list of required technical indicators for this strategy"""
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate that data contains required indicators"""
        required = self.get_required_indicators()
        return all(indicator in data.columns for indicator in required)
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, 
                      slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD, Signal line, and Histogram"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, 
                                std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    def add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add common technical indicators to data"""
        df = data.copy()
        
        # Moving Averages
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        df['EMA_12'] = df['close'].ewm(span=12).mean()
        df['EMA_26'] = df['close'].ewm(span=26).mean()
        
        # RSI
        df['RSI'] = self.calculate_rsi(df['close'])
        
        # MACD
        macd, signal_line, histogram = self.calculate_macd(df['close'])
        df['MACD'] = macd
        df['MACD_Signal'] = signal_line
        df['MACD_Histogram'] = histogram
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(df['close'])
        df['BB_Upper'] = bb_upper
        df['BB_Middle'] = bb_middle
        df['BB_Lower'] = bb_lower
        
        # Volume indicators
        df['Volume_SMA'] = df['volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['volume'] / df['Volume_SMA']
        
        return df
    
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