"""
Test for Profit Calculator
Unit tests for profit calculation algorithms
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.profit_calculator import ProfitCalculator


class TestProfitCalculator:
    """Profit Calculator test sınıfı"""
    
    def setup_method(self):
        """Her test öncesi çalışır"""
        self.calculator = ProfitCalculator(initial_capital=10000.0)
    
    def test_initialization(self):
        """Başlangıç değerleri testi"""
        assert self.calculator.initial_capital == 10000.0
        assert self.calculator.current_capital == 10000.0
        assert self.calculator.daily_target_profit == 0.01
        assert len(self.calculator.trade_history) == 0
    
    def test_compound_profit_calculation(self):
        """Bileşik kazanç hesaplama testi"""
        # 30 günde %1 günlük kazanç
        result = self.calculator.calculate_compound_profit(30, 0.01)
        expected = (1.01 ** 30) - 1  # Approximately 0.348 (34.8%)
        
        assert abs(result - expected) < 0.001
        assert result > 0.34  # En az %34 kazanç olmalı
        assert result < 0.35  # %35'ten az olmalı
    
    def test_monthly_target_capital(self):
        """Aylık hedef sermaye testi"""
        # 1. ay hedefi
        target_1 = self.calculator.get_monthly_target_capital(1)
        expected_1 = 10000.0 * (1 + 0.348)  # %34.8 kazanç
        assert abs(target_1 - expected_1) < 0.01
        
        # 2. ay hedefi
        target_2 = self.calculator.get_monthly_target_capital(2)
        expected_2 = 10000.0 * (1 + 0.80)   # %80 kazanç
        assert abs(target_2 - expected_2) < 0.01
    
    def test_position_size_calculation(self):
        """Position size hesaplama testi"""
        current_capital = 12000.0
        risk_percentage = 0.02  # %2
        
        position_size = self.calculator.calculate_position_size(current_capital, risk_percentage)
        expected = current_capital * risk_percentage
        
        assert position_size == expected
        assert position_size == 240.0  # 12000 * 0.02
    
    def test_trade_recording(self):
        """Trade kayıt testi"""
        # Kazançlı trade
        trade = self.calculator.record_trade(
            trade_type='BUY',
            symbol='BTC/USDT',
            amount=0.1,
            entry_price=50000.0,
            exit_price=51000.0,
            profit_loss=100.0
        )
        
        assert trade['type'] == 'BUY'
        assert trade['symbol'] == 'BTC/USDT'
        assert trade['profit_loss'] == 100.0
        assert self.calculator.current_capital == 10100.0
        assert len(self.calculator.trade_history) == 1
    
    def test_daily_performance(self):
        """Günlük performans testi"""
        # Bugün için bir trade kaydet
        today = datetime.now()
        
        self.calculator.record_trade(
            'BUY', 'ETH/USDT', 1.0, 3000.0, 3030.0, 30.0
        )
        
        performance = self.calculator.get_daily_performance(today.date())
        
        assert performance['trades_count'] == 1
        assert performance['total_profit'] == 30.0
        assert performance['profit_rate'] == 0.003  # 30/10000 = 0.3%
        assert not performance['target_achieved']  # %0.3 < %1 hedef
    
    def test_daily_target_calculation(self):
        """Dinamik günlük hedef testi"""
        # 15. gün, %0.5 kazanç elde edilmiş (hedefin gerisinde)
        current_day = 15
        days_in_month = 30
        achieved_profit_rate = 0.005  # %0.5
        
        daily_target = self.calculator.calculate_daily_target(
            current_day, days_in_month, achieved_profit_rate
        )
        
        # Eksik kazanç kalan günlere dağıtılmalı
        assert daily_target > 0.01  # Normal %1'den fazla olmalı
    
    def test_required_daily_profit(self):
        """Gerekli günlük kazanç hesaplama testi"""
        # Sermayeyi biraz artır
        self.calculator.current_capital = 11000.0  # %10 kazanç
        
        current_day = 20
        month = 1
        
        required_profit = self.calculator.calculate_required_daily_profit(current_day, month)
        
        # Pozitif bir değer dönmeli
        assert required_profit >= 0
    
    def test_performance_summary(self):
        """Performans özeti testi"""
        # Birkaç trade ekle
        trades_data = [
            ('BUY', 'BTC/USDT', 0.1, 50000, 51000, 100),   # Kazançlı
            ('SELL', 'ETH/USDT', 1.0, 3000, 2950, -50),    # Zararlı
            ('BUY', 'AAPL', 10, 150, 155, 50)              # Kazançlı
        ]
        
        for trade_type, symbol, amount, entry, exit, pnl in trades_data:
            self.calculator.record_trade(trade_type, symbol, amount, entry, exit, pnl)
        
        summary = self.calculator.get_performance_summary()
        
        assert summary['total_trades'] == 3
        assert summary['total_profit'] == 100.0  # 100 - 50 + 50
        assert summary['win_rate'] == 2/3  # 2 kazançlı, 1 zararlı
        assert summary['current_capital'] == 10100.0
    
    def test_monthly_performance(self):
        """Aylık performans testi"""
        # Bu ay için trade'ler ekle
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        self.calculator.record_trade('BUY', 'BTC/USDT', 0.1, 50000, 51000, 100)
        
        monthly_perf = self.calculator.get_monthly_performance(current_month, current_year)
        
        assert monthly_perf['month'] == current_month
        assert monthly_perf['year'] == current_year
        assert monthly_perf['trades_count'] == 1
        assert monthly_perf['total_profit'] == 100.0
        assert monthly_perf['profit_rate'] == 0.01  # 100/10000 = 1%
        
        # 1. ay hedefi %34.8
        if current_month == 1:
            assert monthly_perf['target_rate'] == 0.348
            assert not monthly_perf['target_achieved']  # %1 < %34.8


class TestProfitCalculatorEdgeCases:
    """Edge case testleri"""
    
    def test_zero_capital(self):
        """Sıfır sermaye testi"""
        calculator = ProfitCalculator(initial_capital=0.0)
        
        # Position size hesaplama
        position_size = calculator.calculate_position_size(0.0, 0.02)
        assert position_size == 0.0
        
        # Performance summary
        summary = calculator.get_performance_summary()
        assert summary['total_profit_rate'] == 0
    
    def test_negative_profit(self):
        """Negatif kar testi"""
        calculator = ProfitCalculator(initial_capital=10000.0)
        
        # Zararlı trade
        calculator.record_trade('BUY', 'TEST', 1.0, 100, 90, -10)
        
        assert calculator.current_capital == 9990.0
        
        summary = calculator.get_performance_summary()
        assert summary['total_profit'] == -10.0
        assert summary['total_profit_rate'] == -0.001  # -0.1%
    
    def test_large_capital_amounts(self):
        """Büyük sermaye miktarları testi"""
        calculator = ProfitCalculator(initial_capital=1000000.0)  # 1M
        
        position_size = calculator.calculate_position_size(1000000.0, 0.02)
        assert position_size == 20000.0  # 2% of 1M
        
        # Compound profit
        result = calculator.calculate_compound_profit(30, 0.01)
        assert result > 0.34
    
    def test_extreme_daily_targets(self):
        """Aşırı günlük hedefler testi"""
        calculator = ProfitCalculator(initial_capital=10000.0)
        
        # 29. gün, hiç kazanç yok (son gün kaldığında)
        daily_target = calculator.calculate_daily_target(
            current_day=29, 
            days_in_month=30, 
            achieved_profit_rate=0.0
        )
        
        # Çok yüksek bir hedef çıkmalı ama makul sınırlar içinde
        assert daily_target >= 0.01  # En az normal hedef kadar
        assert daily_target < 1.0  # %100'den az olmalı


if __name__ == '__main__':
    pytest.main([__file__, '-v'])