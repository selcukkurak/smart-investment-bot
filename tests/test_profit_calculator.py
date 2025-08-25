"""
Tests for Smart Investment Bot - Profit Calculator
"""

import pytest
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from src.core.profit_calculator import ProfitCalculator


class TestProfitCalculator:
    """Test cases for ProfitCalculator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.initial_capital = 10000
        self.calc = ProfitCalculator(self.initial_capital)
    
    def test_initialization(self):
        """Test profit calculator initialization"""
        assert self.calc.initial_capital == 10000
        assert self.calc.current_capital == 10000
        assert self.calc.daily_target_rate == 0.01
        assert len(self.calc.daily_performance) == 0
    
    def test_daily_target_calculation(self):
        """Test daily 1% target calculation"""
        target = self.calc.calculate_daily_target(10000)
        assert target == 100  # 1% of 10000
        
        target = self.calc.calculate_daily_target(15000)
        assert target == 150  # 1% of 15000
    
    def test_monthly_compound_target(self):
        """Test monthly compound growth calculation"""
        # 30 days at 1% daily should be approximately 34.78%
        result = self.calc.calculate_monthly_compound_target(30)
        expected = 10000 * (1.01 ** 30)  # About 13478
        assert abs(result - expected) < 1
        
        # Verify compound formula
        assert result > 13400  # Should be significant compound growth
        assert result < 13500
    
    def test_track_daily_performance_success(self):
        """Test tracking successful daily performance"""
        date = datetime.now()
        opening = 10000
        closing = 10105  # 1.05% gain, above 1% target
        
        performance = self.calc.track_daily_performance(date, opening, closing, [])
        
        assert performance['opening_balance'] == 10000
        assert performance['closing_balance'] == 10105
        assert performance['daily_return'] == 105
        assert performance['daily_return_rate'] == 0.0105
        assert performance['target_amount'] == 100
        assert performance['target_met'] == True
        assert self.calc.current_capital == 10105
    
    def test_track_daily_performance_failure(self):
        """Test tracking failed daily performance"""
        date = datetime.now()
        opening = 10000
        closing = 10050  # 0.5% gain, below 1% target
        
        performance = self.calc.track_daily_performance(date, opening, closing, [])
        
        assert performance['daily_return'] == 50
        assert performance['daily_return_rate'] == 0.005
        assert performance['target_met'] == False
    
    def test_missed_target_compensation(self):
        """Test compensation calculation for missed targets"""
        # If 10 days failed and 20 days remaining
        compensation_rate = self.calc.calculate_missed_target_compensation(10, 20)
        
        # Should be higher than normal 1% to compensate
        assert compensation_rate > 0.01
        assert compensation_rate <= 0.03  # But capped at 3%
        
        # If no remaining days, should return normal rate
        compensation_rate = self.calc.calculate_missed_target_compensation(10, 0)
        assert compensation_rate == 0.01
    
    def test_monthly_summary(self):
        """Test monthly performance summary"""
        # Add some daily performances
        for i in range(5):
            date = datetime(2024, 1, i+1)
            opening = 10000 + (i * 100)
            closing = opening + 100  # $100 gain each day
            self.calc.track_daily_performance(date, opening, closing, [])
        
        summary = self.calc.get_monthly_summary(1, 2024)
        
        assert summary['month'] == '2024-01'
        assert summary['days_traded'] == 5
        assert summary['total_return'] > 0
        assert 'target_success_rate' in summary
    
    def test_dynamic_target_adjustment(self):
        """Test dynamic target adjustment based on recent performance"""
        # Simulate 12 failed days in current month
        current_date = datetime.now()
        
        for i in range(12):
            date = current_date.replace(day=i+1)
            opening = 10000
            closing = 10050  # Only 0.5% gain (below 1% target)
            self.calc.track_daily_performance(date, opening, closing, [])
        
        # Check dynamic target for day 15
        test_date = current_date.replace(day=15)
        dynamic_target = self.calc.get_dynamic_target_for_date(test_date)
        
        # Should be higher than normal 1% due to compensation
        assert dynamic_target > 0.01
    
    def test_performance_report(self):
        """Test comprehensive performance report"""
        # Add some performance data
        for i in range(3):
            date = datetime.now() - timedelta(days=2-i)
            opening = 10000 + (i * 100)
            closing = opening + 110  # Good returns
            self.calc.track_daily_performance(date, opening, closing, [])
        
        report = self.calc.get_performance_report()
        
        assert report['initial_capital'] == 10000
        assert report['total_days'] == 3
        assert report['total_return'] > 0
        assert 'target_success_rate' in report
        assert 'daily_performance' in report
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Test with zero opening balance
        performance = self.calc.track_daily_performance(
            datetime.now(), 0, 100, []
        )
        assert performance['daily_return_rate'] == 0  # Should handle division by zero
        
        # Test empty performance report
        empty_calc = ProfitCalculator(5000)
        report = empty_calc.get_performance_report()
        assert report['total_days'] == 0
        assert report['current_capital'] == 5000