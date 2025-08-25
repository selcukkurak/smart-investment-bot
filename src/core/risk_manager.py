"""
Smart Investment Bot - Risk Manager
Manages trading risks with daily loss limits and position sizing
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class RiskManager:
    """
    Manages trading risks including position sizing, stop losses, and daily limits
    """
    
    def __init__(self, max_daily_loss_rate: float = 0.02, 
                 max_position_rate: float = 0.1,
                 max_drawdown_rate: float = 0.05):
        self.max_daily_loss_rate = max_daily_loss_rate  # 2% max daily loss
        self.max_position_rate = max_position_rate       # 10% max per position
        self.max_drawdown_rate = max_drawdown_rate       # 5% max drawdown
        self.daily_losses: Dict[str, float] = {}
        self.peak_capital = 0
        self.current_positions: List[Dict] = []
        
    def calculate_position_size(self, account_balance: float, 
                              risk_per_trade: float = 0.02) -> float:
        """
        Calculate optimal position size based on account balance and risk
        """
        # Maximum position size based on account balance
        max_position_by_balance = account_balance * self.max_position_rate
        
        # Risk-based position sizing (2% risk per trade)
        risk_based_position = account_balance * risk_per_trade
        
        # Use the smaller of the two
        return min(max_position_by_balance, risk_based_position)
    
    def calculate_stop_loss_price(self, entry_price: float, 
                                position_type: str,
                                stop_loss_percent: float = 0.02) -> float:
        """
        Calculate stop loss price based on entry price and risk percentage
        """
        if position_type.lower() == 'long':
            return entry_price * (1 - stop_loss_percent)
        elif position_type.lower() == 'short':
            return entry_price * (1 + stop_loss_percent)
        else:
            raise ValueError("Position type must be 'long' or 'short'")
    
    def calculate_take_profit_price(self, entry_price: float,
                                  position_type: str,
                                  take_profit_percent: float = 0.03) -> float:
        """
        Calculate take profit price based on entry price and target percentage
        """
        if position_type.lower() == 'long':
            return entry_price * (1 + take_profit_percent)
        elif position_type.lower() == 'short':
            return entry_price * (1 - take_profit_percent)
        else:
            raise ValueError("Position type must be 'long' or 'short'")
    
    def check_daily_loss_limit(self, current_balance: float, 
                             opening_balance: float,
                             date: Optional[datetime] = None) -> Tuple[bool, float]:
        """
        Check if daily loss limit has been reached
        Returns: (can_trade, current_daily_loss)
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime('%Y-%m-%d')
        
        daily_loss = opening_balance - current_balance
        daily_loss_rate = daily_loss / opening_balance if opening_balance > 0 else 0
        
        # Store daily loss
        self.daily_losses[date_str] = daily_loss
        
        # Check if loss limit exceeded
        can_trade = daily_loss_rate < self.max_daily_loss_rate
        
        return can_trade, daily_loss
    
    def check_drawdown_limit(self, current_balance: float) -> Tuple[bool, float]:
        """
        Check if maximum drawdown limit has been reached
        Returns: (can_trade, current_drawdown)
        """
        if self.peak_capital == 0:
            self.peak_capital = current_balance
        
        # Update peak if current balance is higher
        if current_balance > self.peak_capital:
            self.peak_capital = current_balance
        
        # Calculate drawdown
        drawdown = (self.peak_capital - current_balance) / self.peak_capital
        can_trade = drawdown < self.max_drawdown_rate
        
        return can_trade, drawdown
    
    def assess_market_risk(self, volatility: float, volume: float, 
                         price_change_24h: float) -> RiskLevel:
        """
        Assess market risk based on volatility, volume, and price movement
        """
        risk_score = 0
        
        # Volatility scoring (higher volatility = higher risk)
        if volatility > 0.05:  # 5%+ volatility
            risk_score += 2
        elif volatility > 0.03:  # 3-5% volatility
            risk_score += 1
        
        # Volume scoring (very low volume = higher risk)
        if volume < 0.5:  # Relative to average volume
            risk_score += 1
        
        # Price change scoring (large moves = higher risk)
        abs_price_change = abs(price_change_24h)
        if abs_price_change > 0.10:  # 10%+ daily change
            risk_score += 2
        elif abs_price_change > 0.05:  # 5-10% daily change
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 4:
            return RiskLevel.EXTREME
        elif risk_score >= 3:
            return RiskLevel.HIGH
        elif risk_score >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def get_risk_adjusted_position_size(self, base_position_size: float,
                                      risk_level: RiskLevel) -> float:
        """
        Adjust position size based on market risk assessment
        """
        risk_multipliers = {
            RiskLevel.LOW: 1.0,      # Full position size
            RiskLevel.MEDIUM: 0.75,  # 75% of position
            RiskLevel.HIGH: 0.5,     # 50% of position
            RiskLevel.EXTREME: 0.25  # 25% of position
        }
        
        return base_position_size * risk_multipliers[risk_level]
    
    def should_allow_trade(self, current_balance: float, opening_balance: float,
                         position_size: float, asset_type: str = "crypto") -> Tuple[bool, str]:
        """
        Comprehensive check if a trade should be allowed
        Returns: (allowed, reason)
        """
        # Check daily loss limit
        can_trade_daily, daily_loss = self.check_daily_loss_limit(
            current_balance, opening_balance
        )
        if not can_trade_daily:
            return False, f"Daily loss limit reached: {daily_loss:.2f} ({self.max_daily_loss_rate*100}% max)"
        
        # Check drawdown limit
        can_trade_drawdown, drawdown = self.check_drawdown_limit(current_balance)
        if not can_trade_drawdown:
            return False, f"Drawdown limit reached: {drawdown:.2%} ({self.max_drawdown_rate:.2%} max)"
        
        # Check position size limits
        max_allowed_position = current_balance * self.max_position_rate
        if position_size > max_allowed_position:
            return False, f"Position size too large: {position_size:.2f} > {max_allowed_position:.2f}"
        
        # Check maximum number of positions
        if len(self.current_positions) >= 5:  # Max 5 simultaneous positions
            return False, "Maximum number of positions reached (5)"
        
        return True, "Trade allowed"
    
    def add_position(self, symbol: str, position_type: str, entry_price: float,
                    quantity: float, stop_loss: float, take_profit: float) -> str:
        """
        Add a new position to tracking
        """
        position_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        position = {
            'id': position_id,
            'symbol': symbol,
            'type': position_type,
            'entry_price': entry_price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_time': datetime.now(),
            'status': 'open'
        }
        
        self.current_positions.append(position)
        return position_id
    
    def close_position(self, position_id: str, exit_price: float, 
                      exit_reason: str = "manual") -> Optional[Dict]:
        """
        Close a position and calculate P&L
        """
        for i, position in enumerate(self.current_positions):
            if position['id'] == position_id:
                # Calculate P&L
                if position['type'].lower() == 'long':
                    pnl = (exit_price - position['entry_price']) * position['quantity']
                else:  # short
                    pnl = (position['entry_price'] - exit_price) * position['quantity']
                
                position['exit_price'] = exit_price
                position['exit_time'] = datetime.now()
                position['pnl'] = pnl
                position['exit_reason'] = exit_reason
                position['status'] = 'closed'
                
                # Remove from active positions
                closed_position = self.current_positions.pop(i)
                return closed_position
        
        return None
    
    def get_risk_metrics(self, current_balance: float) -> Dict:
        """
        Get current risk metrics and status
        """
        today = datetime.now().strftime('%Y-%m-%d')
        daily_loss = self.daily_losses.get(today, 0)
        
        can_trade_daily, _ = self.check_daily_loss_limit(current_balance, current_balance)
        can_trade_drawdown, drawdown = self.check_drawdown_limit(current_balance)
        
        return {
            'current_balance': current_balance,
            'peak_capital': self.peak_capital,
            'daily_loss': daily_loss,
            'daily_loss_rate': daily_loss / current_balance if current_balance > 0 else 0,
            'max_daily_loss_rate': self.max_daily_loss_rate,
            'drawdown': drawdown,
            'max_drawdown_rate': self.max_drawdown_rate,
            'can_trade': can_trade_daily and can_trade_drawdown,
            'active_positions': len(self.current_positions),
            'max_positions': 5,
            'available_position_slots': 5 - len(self.current_positions)
        }