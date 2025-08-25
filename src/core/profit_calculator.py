"""
Smart Investment Bot - Profit Calculator
Handles daily 1% profit target calculation and dynamic adjustment system
Uses only standard library - no external dependencies
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional


class ProfitCalculator:
    """
    Calculates profit targets and tracks performance against 1% daily goal
    """
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.daily_target_rate = 0.01  # 1% daily target
        self.monthly_performance: Dict[str, Dict] = {}
        self.daily_performance: List[Dict] = []
        
    def calculate_daily_target(self, current_balance: float) -> float:
        """Calculate 1% daily profit target on current balance"""
        return current_balance * self.daily_target_rate
    
    def calculate_monthly_compound_target(self, days: int) -> float:
        """
        Calculate expected compound growth for given days
        Formula: initial_capital * (1.01)^days
        """
        return self.initial_capital * (1.01 ** days)
    
    def get_monthly_expected_return(self, month: int, year: int) -> float:
        """
        Calculate expected monthly return
        Month 1: ~34.8% (1.01^30 ≈ 1.348)
        Month 2: ~81.4% compound ((1.01^30)^2 ≈ 1.814)
        """
        # Assume 30 trading days per month
        trading_days = 30
        total_days = month * trading_days
        return self.calculate_monthly_compound_target(total_days)
    
    def track_daily_performance(self, date: datetime, opening_balance: float, 
                              closing_balance: float, trades: List[Dict]) -> Dict:
        """
        Track daily performance against target
        """
        daily_return = closing_balance - opening_balance
        daily_return_rate = daily_return / opening_balance if opening_balance > 0 else 0
        target_amount = self.calculate_daily_target(opening_balance)
        target_met = daily_return >= target_amount
        
        performance = {
            'date': date.strftime('%Y-%m-%d'),
            'opening_balance': opening_balance,
            'closing_balance': closing_balance,
            'daily_return': daily_return,
            'daily_return_rate': daily_return_rate,
            'target_amount': target_amount,
            'target_rate': self.daily_target_rate,
            'target_met': target_met,
            'trades_count': len(trades),
            'trades': trades
        }
        
        self.daily_performance.append(performance)
        self.current_capital = closing_balance
        
        return performance
    
    def calculate_missed_target_compensation(self, days_failed: int, 
                                           remaining_days: int) -> float:
        """
        Calculate compensation rate for remaining days if targets missed
        If 10 days failed to meet 1% target, compensate in remaining days
        """
        if remaining_days <= 0:
            return self.daily_target_rate
        
        # Calculate total missed profit (approximately)
        missed_profit_rate = days_failed * self.daily_target_rate
        
        # Distribute over remaining days with slight buffer
        compensation_rate = self.daily_target_rate + (missed_profit_rate / remaining_days)
        
        # Cap at reasonable maximum (e.g., 3% daily max)
        max_daily_rate = 0.03
        return min(compensation_rate, max_daily_rate)
    
    def get_monthly_summary(self, month: int, year: int) -> Dict:
        """
        Generate monthly performance summary
        """
        month_str = f"{year}-{month:02d}"
        
        # Filter daily performance for the month
        month_performance = [
            p for p in self.daily_performance 
            if p['date'].startswith(month_str)
        ]
        
        if not month_performance:
            return {
                'month': month_str,
                'days_traded': 0,
                'targets_met': 0,
                'total_return': 0,
                'expected_return': 0,
                'performance_ratio': 0
            }
        
        days_traded = len(month_performance)
        targets_met = sum(1 for p in month_performance if p['target_met'])
        
        opening_balance = month_performance[0]['opening_balance']
        closing_balance = month_performance[-1]['closing_balance']
        total_return = closing_balance - opening_balance
        
        expected_return = self.calculate_monthly_compound_target(days_traded) - self.initial_capital
        performance_ratio = total_return / expected_return if expected_return > 0 else 0
        
        summary = {
            'month': month_str,
            'days_traded': days_traded,
            'targets_met': targets_met,
            'target_success_rate': targets_met / days_traded if days_traded > 0 else 0,
            'opening_balance': opening_balance,
            'closing_balance': closing_balance,
            'total_return': total_return,
            'total_return_rate': total_return / opening_balance if opening_balance > 0 else 0,
            'expected_return': expected_return,
            'performance_ratio': performance_ratio,
            'avg_daily_return': total_return / days_traded if days_traded > 0 else 0
        }
        
        self.monthly_performance[month_str] = summary
        return summary
    
    def get_dynamic_target_for_date(self, target_date: datetime) -> float:
        """
        Calculate dynamic target for a specific date based on recent performance
        """
        # Get performance for current month
        current_month = target_date.month
        current_year = target_date.year
        month_str = f"{current_year}-{current_month:02d}"
        
        # Count failed days in current month
        month_performance = [
            p for p in self.daily_performance 
            if p['date'].startswith(month_str) and 
            datetime.strptime(p['date'], '%Y-%m-%d') < target_date
        ]
        
        failed_days = sum(1 for p in month_performance if not p['target_met'])
        
        # If more than 10 days failed, apply compensation
        if failed_days >= 10:
            # Calculate remaining days in month (assume 30 trading days)
            days_passed = len(month_performance)
            remaining_days = 30 - days_passed
            
            if remaining_days > 0:
                compensation_rate = self.calculate_missed_target_compensation(
                    failed_days, remaining_days
                )
                return compensation_rate
        
        return self.daily_target_rate
    
    def get_performance_report(self) -> Dict:
        """
        Generate comprehensive performance report
        """
        if not self.daily_performance:
            return {
                'total_days': 0,
                'current_capital': self.current_capital,
                'total_return': 0,
                'total_return_rate': 0
            }
        
        total_days = len(self.daily_performance)
        targets_met = sum(1 for p in self.daily_performance if p['target_met'])
        total_return = self.current_capital - self.initial_capital
        total_return_rate = total_return / self.initial_capital
        
        expected_total = self.calculate_monthly_compound_target(total_days)
        expected_return = expected_total - self.initial_capital
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'total_days': total_days,
            'targets_met': targets_met,
            'target_success_rate': targets_met / total_days if total_days > 0 else 0,
            'total_return': total_return,
            'total_return_rate': total_return_rate,
            'expected_return': expected_return,
            'expected_return_rate': expected_return / self.initial_capital,
            'performance_vs_target': total_return / expected_return if expected_return > 0 else 0,
            'daily_performance': self.daily_performance[-7:],  # Last 7 days
            'monthly_summaries': list(self.monthly_performance.values())
        }