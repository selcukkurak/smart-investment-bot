"""
Smart Investment Bot - Scalping Strategy Implementation
High-frequency trading strategy for quick profits
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .base_strategy import BaseStrategy, Signal, SignalType


class ScalpingStrategy(BaseStrategy):
    """
    Scalping strategy implementation focusing on quick profits
    from small price movements using RSI, MACD, and volume analysis
    """
    
    def __init__(self):
        super().__init__(
            name="Advanced Scalping",
            timeframes=["1m", "5m"],
            min_confidence=0.65
        )
        
        # Scalping-specific parameters
        self.rsi_oversold = 25      # More aggressive oversold level
        self.rsi_overbought = 75    # More aggressive overbought level
        self.volume_spike_threshold = 2.0  # 2x average volume
        self.quick_profit_target = 0.5     # 0.5% quick profit
        self.tight_stop_loss = 0.25        # 0.25% stop loss
        
    def get_required_indicators(self) -> List[str]:
        """Required indicators for scalping strategy"""
        return [
            'RSI', 'MACD', 'MACD_Signal', 'MACD_Histogram',
            'Volume_Ratio', 'SMA_20', 'EMA_12', 'BB_Upper', 'BB_Lower'
        ]
    
    def analyze(self, symbol: str, data: List[Dict]) -> Signal:
        """
        Advanced scalping analysis with multiple confirmation signals
        """
        if not self.validate_data(data) or len(data) < 50:
            return Signal(SignalType.HOLD, 0.0, 0.0, "Insufficient data for scalping", {})
        
        # Add indicators if not present
        if 'RSI' not in data[-1]:
            data = self.add_technical_indicators(data)
        
        # Get recent data points
        latest = data[-1]
        prev1 = data[-2] if len(data) > 1 else latest
        prev2 = data[-3] if len(data) > 2 else latest
        
        current_price = latest.get('close', latest.get('price', 0))
        
        # Extract indicators with safe defaults
        rsi = latest.get('RSI')
        macd = latest.get('MACD')
        macd_signal = latest.get('MACD_Signal')
        macd_hist = latest.get('MACD_Histogram')
        volume_ratio = latest.get('Volume_Ratio', 1.0)
        sma_20 = latest.get('SMA_20')
        ema_12 = latest.get('EMA_12')
        bb_upper = latest.get('BB_Upper')
        bb_lower = latest.get('BB_Lower')
        
        # Initialize scoring system
        buy_score = 0
        sell_score = 0
        confidence_components = []
        reasoning_parts = []
        
        # 1. RSI Analysis (Primary Signal)
        if rsi is not None:
            if rsi <= self.rsi_oversold:
                buy_score += 3
                confidence_components.append(0.3)
                reasoning_parts.append(f"RSI extremely oversold ({rsi:.1f})")
            elif rsi <= 35:
                buy_score += 2
                confidence_components.append(0.2)
                reasoning_parts.append(f"RSI oversold ({rsi:.1f})")
            elif rsi >= self.rsi_overbought:
                sell_score += 3
                confidence_components.append(0.3)
                reasoning_parts.append(f"RSI extremely overbought ({rsi:.1f})")
            elif rsi >= 65:
                sell_score += 2
                confidence_components.append(0.2)
                reasoning_parts.append(f"RSI overbought ({rsi:.1f})")
        
        # 2. MACD Analysis (Momentum Confirmation)
        if macd is not None and macd_signal is not None:
            macd_prev = prev1.get('MACD', macd)
            macd_signal_prev = prev1.get('MACD_Signal', macd_signal)
            
            # Bullish crossover
            if macd > macd_signal and macd_prev <= macd_signal_prev:
                buy_score += 2
                confidence_components.append(0.25)
                reasoning_parts.append("MACD bullish crossover")
            # Bearish crossover
            elif macd < macd_signal and macd_prev >= macd_signal_prev:
                sell_score += 2
                confidence_components.append(0.25)
                reasoning_parts.append("MACD bearish crossover")
            
            # MACD histogram momentum
            if macd_hist is not None:
                macd_hist_prev = prev1.get('MACD_Histogram', macd_hist)
                if macd_hist > 0 and macd_hist > macd_hist_prev:
                    buy_score += 1
                    confidence_components.append(0.1)
                    reasoning_parts.append("MACD momentum increasing")
                elif macd_hist < 0 and macd_hist < macd_hist_prev:
                    sell_score += 1
                    confidence_components.append(0.1)
                    reasoning_parts.append("MACD momentum decreasing")
        
        # 3. Volume Confirmation (Critical for scalping)
        if pd.notna(volume_ratio) and volume_ratio >= self.volume_spike_threshold:
            if buy_score > sell_score:
                buy_score += 1
                confidence_components.append(0.2)
                reasoning_parts.append(f"Volume spike confirms bullish ({volume_ratio:.1f}x)")
            elif sell_score > buy_score:
                sell_score += 1
                confidence_components.append(0.2)
                reasoning_parts.append(f"Volume spike confirms bearish ({volume_ratio:.1f}x)")
        
        # 4. Price Action Analysis
        if pd.notna(sma_20):
            if current_price > sma_20 * 1.002:  # 0.2% above SMA
                buy_score += 0.5
                reasoning_parts.append("Price above SMA20 trend")
            elif current_price < sma_20 * 0.998:  # 0.2% below SMA
                sell_score += 0.5
                reasoning_parts.append("Price below SMA20 trend")
        
        # 5. Bollinger Bands (Support/Resistance)
        if pd.notna(bb_upper) and pd.notna(bb_lower):
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
            
            if bb_position <= 0.1:  # Near lower band
                buy_score += 1
                confidence_components.append(0.15)
                reasoning_parts.append("Near Bollinger lower band")
            elif bb_position >= 0.9:  # Near upper band
                sell_score += 1
                confidence_components.append(0.15)
                reasoning_parts.append("Near Bollinger upper band")
        
        # 6. Short-term momentum (for scalping)
        if len(data) >= 5:
            recent_prices = data['close'].tail(5)
            momentum = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0] * 100
            
            if momentum > 0.3:  # 0.3% upward momentum
                buy_score += 0.5
                reasoning_parts.append(f"Bullish momentum ({momentum:.2f}%)")
            elif momentum < -0.3:  # 0.3% downward momentum
                sell_score += 0.5
                reasoning_parts.append(f"Bearish momentum ({momentum:.2f}%)")
        
        # Determine final signal
        net_score = buy_score - sell_score
        
        if net_score >= 3 and buy_score >= 4:
            signal_type = SignalType.BUY
            confidence = min(sum(confidence_components), 0.95)
        elif net_score <= -3 and sell_score >= 4:
            signal_type = SignalType.SELL
            confidence = min(sum(confidence_components), 0.95)
        else:
            signal_type = SignalType.HOLD
            confidence = 0.0
        
        # Only return signal if confidence meets minimum threshold
        if confidence < self.min_confidence and signal_type != SignalType.HOLD:
            signal_type = SignalType.HOLD
            confidence = 0.0
            reasoning_parts.append(f"Confidence too low ({confidence:.2f} < {self.min_confidence})")
        
        reasoning = f"Scalping: {', '.join(reasoning_parts) if reasoning_parts else 'No actionable signals'}"
        
        indicators = {
            'RSI': float(rsi) if pd.notna(rsi) else None,
            'MACD': float(macd) if pd.notna(macd) else None,
            'MACD_Signal': float(macd_signal) if pd.notna(macd_signal) else None,
            'MACD_Histogram': float(macd_hist) if pd.notna(macd_hist) else None,
            'Volume_Ratio': float(volume_ratio) if pd.notna(volume_ratio) else None,
            'SMA_20': float(sma_20) if pd.notna(sma_20) else None,
            'EMA_12': float(ema_12) if pd.notna(ema_12) else None,
            'BB_Upper': float(bb_upper) if pd.notna(bb_upper) else None,
            'BB_Lower': float(bb_lower) if pd.notna(bb_lower) else None,
            'Buy_Score': buy_score,
            'Sell_Score': sell_score,
            'Net_Score': net_score
        }
        
        signal = Signal(signal_type, confidence, current_price, reasoning, indicators)
        self.record_signal(signal)
        
        return signal
    
    def get_scalping_targets(self, entry_price: float, position_type: str) -> Dict[str, float]:
        """
        Calculate scalping-specific targets
        """
        if position_type.lower() == 'long':
            return {
                'quick_target_1': entry_price * (1 + self.quick_profit_target / 100),  # 0.5%
                'quick_target_2': entry_price * (1 + (self.quick_profit_target * 1.5) / 100),  # 0.75%
                'stop_loss': entry_price * (1 - self.tight_stop_loss / 100)  # 0.25%
            }
        else:  # short
            return {
                'quick_target_1': entry_price * (1 - self.quick_profit_target / 100),
                'quick_target_2': entry_price * (1 - (self.quick_profit_target * 1.5) / 100),
                'stop_loss': entry_price * (1 + self.tight_stop_loss / 100)
            }
    
    def is_scalping_opportunity(self, data: List[Dict], min_volatility: float = 0.01) -> bool:
        """
        Check if current market conditions are suitable for scalping
        """
        if len(data) < 20:
            return False
        
        # Extract prices for volatility calculation
        prices = [d.get('close', d.get('price', 0)) for d in data[-20:]]
        volumes = [d.get('volume', 1) for d in data[-20:]]
        
        # Check recent volatility
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5
        
        # Check volume activity
        avg_volume = sum(volumes) / len(volumes)
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Scalping is good when:
        # 1. Moderate volatility (not too high, not too low)
        # 2. Good volume activity
        # 3. Clear price movements
        
        conditions_met = (
            min_volatility <= volatility <= 0.05 and  # Moderate volatility
            volume_ratio >= 0.8 and                   # Decent volume
            prices[-1] > 0                             # Valid price data
        )
        
        return conditions_met