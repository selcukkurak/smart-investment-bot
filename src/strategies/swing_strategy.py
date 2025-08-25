"""
Smart Investment Bot - Swing Trading Strategy
Medium-term trading strategy for trend following
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..strategies.base_strategy import BaseStrategy, Signal, SignalType


class SwingStrategy(BaseStrategy):
    """
    Swing trading strategy for medium-term positions (hours to days)
    Uses trend analysis, moving averages, and momentum indicators
    """
    
    def __init__(self):
        super().__init__(
            name="Swing Trading",
            timeframes=["1h", "4h", "1d"],
            min_confidence=0.6
        )
        
        # Swing trading parameters
        self.trend_confirmation_period = 3  # Days to confirm trend
        self.momentum_threshold = 0.02      # 2% momentum threshold
        self.profit_target = 0.05           # 5% profit target
        self.stop_loss = 0.03               # 3% stop loss
    
    def get_required_indicators(self) -> List[str]:
        """Required indicators for swing strategy"""
        return [
            'SMA_20', 'SMA_50', 'EMA_12', 'EMA_26',
            'MACD', 'MACD_Signal', 'BB_Upper', 'BB_Lower',
            'Volume_Ratio', 'RSI'
        ]
    
    def analyze(self, symbol: str, data) -> Signal:
        """
        Analyze data for swing trading opportunities
        Note: Using simplified data structure due to pandas unavailability
        """
        if not isinstance(data, list) or len(data) < 50:
            return Signal(SignalType.HOLD, 0.0, 0.0, "Insufficient data for swing analysis", {})
        
        # Extract price data (assuming data is list of dicts with OHLCV)
        if isinstance(data[0], dict):
            prices = [d.get('close', d.get('price', 0)) for d in data]
            volumes = [d.get('volume', 0) for d in data]
        else:
            # If it's a simple list of prices
            prices = data
            volumes = [1] * len(prices)  # Default volume
        
        if not prices or len(prices) < 50:
            return Signal(SignalType.HOLD, 0.0, 0.0, "Insufficient price data", {})
        
        current_price = prices[-1]
        
        # Calculate indicators manually
        sma_20 = self._calculate_sma(prices, 20)
        sma_50 = self._calculate_sma(prices, 50)
        rsi = self._calculate_rsi(prices)
        
        # Initialize scoring
        swing_score = 0
        confidence_components = []
        reasoning_parts = []
        
        # 1. Trend Analysis (Primary for swing trading)
        if sma_20[-1] and sma_50[-1]:
            trend_strength = (sma_20[-1] - sma_50[-1]) / sma_50[-1]
            
            if sma_20[-1] > sma_50[-1]:  # Bullish trend
                if trend_strength > 0.02:  # Strong bullish trend
                    swing_score += 3
                    confidence_components.append(0.4)
                    reasoning_parts.append(f"Strong bullish trend ({trend_strength:.2%})")
                else:
                    swing_score += 1.5
                    confidence_components.append(0.2)
                    reasoning_parts.append("Weak bullish trend")
            
            elif sma_20[-1] < sma_50[-1]:  # Bearish trend
                if abs(trend_strength) > 0.02:  # Strong bearish trend
                    swing_score -= 3
                    confidence_components.append(0.4)
                    reasoning_parts.append(f"Strong bearish trend ({trend_strength:.2%})")
                else:
                    swing_score -= 1.5
                    confidence_components.append(0.2)
                    reasoning_parts.append("Weak bearish trend")
        
        # 2. Price Position Relative to SMAs
        if sma_20[-1]:
            price_vs_sma20 = (current_price - sma_20[-1]) / sma_20[-1]
            if price_vs_sma20 > 0.01:  # Price 1% above SMA20
                swing_score += 1
                confidence_components.append(0.15)
                reasoning_parts.append("Price above SMA20")
            elif price_vs_sma20 < -0.01:  # Price 1% below SMA20
                swing_score -= 1
                confidence_components.append(0.15)
                reasoning_parts.append("Price below SMA20")
        
        # 3. RSI for entry timing
        if rsi[-1]:
            current_rsi = rsi[-1]
            if 40 <= current_rsi <= 60:  # RSI in middle range (good for swing)
                if swing_score > 0:  # Bullish bias
                    swing_score += 0.5
                    confidence_components.append(0.1)
                    reasoning_parts.append(f"RSI neutral-bullish ({current_rsi:.1f})")
                elif swing_score < 0:  # Bearish bias
                    swing_score -= 0.5
                    confidence_components.append(0.1)
                    reasoning_parts.append(f"RSI neutral-bearish ({current_rsi:.1f})")
            elif current_rsi < 35:  # Oversold
                swing_score += 1
                confidence_components.append(0.2)
                reasoning_parts.append(f"RSI oversold ({current_rsi:.1f})")
            elif current_rsi > 65:  # Overbought
                swing_score -= 1
                confidence_components.append(0.2)
                reasoning_parts.append(f"RSI overbought ({current_rsi:.1f})")
        
        # 4. Momentum Analysis (price change over last few periods)
        if len(prices) >= 10:
            momentum_periods = [3, 5, 10]  # 3, 5, and 10 period momentum
            momentum_signals = []
            
            for period in momentum_periods:
                if len(prices) > period:
                    momentum = (prices[-1] - prices[-period]) / prices[-period]
                    momentum_signals.append(momentum)
            
            avg_momentum = sum(momentum_signals) / len(momentum_signals)
            
            if avg_momentum > self.momentum_threshold:
                swing_score += 1
                confidence_components.append(0.15)
                reasoning_parts.append(f"Positive momentum ({avg_momentum:.2%})")
            elif avg_momentum < -self.momentum_threshold:
                swing_score -= 1
                confidence_components.append(0.15)
                reasoning_parts.append(f"Negative momentum ({avg_momentum:.2%})")
        
        # Determine final signal
        if swing_score >= 2.5:
            signal_type = SignalType.BUY
            confidence = min(sum(confidence_components), 0.9)
        elif swing_score <= -2.5:
            signal_type = SignalType.SELL
            confidence = min(sum(confidence_components), 0.9)
        else:
            signal_type = SignalType.HOLD
            confidence = 0.0
        
        # Apply minimum confidence threshold
        if confidence < self.min_confidence and signal_type != SignalType.HOLD:
            signal_type = SignalType.HOLD
            confidence = 0.0
            reasoning_parts.append(f"Confidence below threshold ({confidence:.2f} < {self.min_confidence})")
        
        reasoning = f"Swing: {', '.join(reasoning_parts) if reasoning_parts else 'No clear trend signals'}"
        
        indicators = {
            'SMA_20': sma_20[-1] if sma_20[-1] else None,
            'SMA_50': sma_50[-1] if sma_50[-1] else None,
            'RSI': rsi[-1] if rsi[-1] else None,
            'Current_Price': current_price,
            'Swing_Score': swing_score,
            'Trend_Strength': abs(swing_score / 3) if swing_score != 0 else 0
        }
        
        signal = Signal(signal_type, confidence, current_price, reasoning, indicators)
        self.record_signal(signal)
        
        return signal
    
    def _calculate_sma(self, prices: List[float], period: int) -> List[Optional[float]]:
        """Calculate Simple Moving Average"""
        sma = []
        for i in range(len(prices)):
            if i < period - 1:
                sma.append(None)
            else:
                avg = sum(prices[i-period+1:i+1]) / period
                sma.append(avg)
        return sma
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> List[Optional[float]]:
        """Calculate RSI"""
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
        
        # Fill remaining positions
        while len(rsi) < len(prices):
            rsi.insert(0, None)
        
        return rsi
    
    def get_swing_targets(self, entry_price: float, position_type: str) -> Dict[str, float]:
        """Calculate swing trading targets"""
        if position_type.lower() == 'long':
            return {
                'profit_target_1': entry_price * (1 + self.profit_target),      # 5%
                'profit_target_2': entry_price * (1 + self.profit_target * 1.5), # 7.5%
                'stop_loss': entry_price * (1 - self.stop_loss)                 # 3%
            }
        else:  # short
            return {
                'profit_target_1': entry_price * (1 - self.profit_target),
                'profit_target_2': entry_price * (1 - self.profit_target * 1.5),
                'stop_loss': entry_price * (1 + self.stop_loss)
            }
    
    def should_hold_position(self, entry_price: float, current_price: float,
                           position_type: str, hold_time_hours: int) -> bool:
        """
        Determine if swing position should be held longer
        Swing trades can be held for hours to days
        """
        # Maximum hold time for swing trades (7 days)
        if hold_time_hours >= 168:  # 7 days
            return False
        
        # Check if still in profit zone
        if position_type.lower() == 'long':
            profit_percent = ((current_price - entry_price) / entry_price) * 100
            # Hold if still profitable and trending up
            return profit_percent > -1.0  # Don't hold if loss > 1%
        else:  # short
            profit_percent = ((entry_price - current_price) / entry_price) * 100
            return profit_percent > -1.0
    
    def analyze_market_structure(self, prices: List[float]) -> Dict[str, Any]:
        """
        Analyze market structure for swing trading suitability
        """
        if len(prices) < 30:
            return {'suitable': False, 'reason': 'Insufficient data'}
        
        # Calculate volatility
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        volatility = (sum(r**2 for r in returns[-20:]) / 20) ** 0.5
        
        # Check for trending market (good for swing)
        sma_20 = self._calculate_sma(prices, 20)
        sma_50 = self._calculate_sma(prices, 50)
        
        trend_clarity = 0
        if sma_20[-1] and sma_50[-1]:
            trend_strength = abs(sma_20[-1] - sma_50[-1]) / sma_50[-1]
            trend_clarity = min(trend_strength / 0.05, 1.0)  # Normalize to 0-1
        
        # Swing trading is suitable when:
        # 1. Moderate volatility (not too choppy, not too flat)
        # 2. Clear trend present
        # 3. Consistent price movement
        
        suitable = (
            0.01 <= volatility <= 0.08 and  # Moderate volatility
            trend_clarity >= 0.3             # Some trend clarity
        )
        
        return {
            'suitable': suitable,
            'volatility': volatility,
            'trend_clarity': trend_clarity,
            'market_condition': 'trending' if trend_clarity > 0.5 else 'choppy' if volatility > 0.05 else 'flat',
            'recommendation': 'good_for_swing' if suitable else 'avoid_swing_trading'
        }