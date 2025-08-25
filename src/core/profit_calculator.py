"""
Profit Calculator - Kazanç hesaplama algoritması
Günlük %1 kazanç hedefi ile dinamik hedef ayarlama
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd


class ProfitCalculator:
    """
    Kazanç hesaplama ve hedef belirleme sınıfı
    
    Özellikler:
    - Günlük %1 kazanç hedefi
    - Dinamik hedef ayarlama
    - Bileşik kazanç hesaplama
    - Aylık hedefler: 1. ay %34.8, 2. ay %80
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.daily_target_profit = 0.01  # %1 günlük hedef
        self.monthly_targets = {1: 0.348, 2: 0.80}  # Aylık hedefler
        self.trade_history: List[Dict] = []
        
    def calculate_daily_target(self, current_day: int, days_in_month: int, 
                             achieved_profit_rate: float) -> float:
        """
        Dinamik günlük hedef hesaplama
        
        Args:
            current_day: Ayın kaçıncı günü
            days_in_month: Aydaki toplam gün sayısı
            achieved_profit_rate: Şu ana kadar elde edilen kazanç oranı
            
        Returns:
            Günlük hedef kazanç oranı
        """
        month = 1 if current_day <= 30 else 2
        target_monthly_profit = self.monthly_targets.get(month, 0.348)
        
        # Kalan günler için gereken kazanç hesaplama
        remaining_days = days_in_month - current_day
        if remaining_days <= 0:
            return self.daily_target_profit
            
        # Eğer hedefin gerisinde isek, kalan günlere eksik kazancı dağıt
        required_total_profit = target_monthly_profit
        if achieved_profit_rate < required_total_profit:
            missing_profit = required_total_profit - achieved_profit_rate
            # Bileşik kazanç formülüne göre günlük hedef ayarlama
            daily_rate_needed = (1 + missing_profit) ** (1/remaining_days) - 1
            return max(daily_rate_needed, self.daily_target_profit)
        
        return self.daily_target_profit
    
    def calculate_compound_profit(self, days: int, daily_rate: float = None) -> float:
        """
        Bileşik kazanç hesaplama: (1 + daily_rate)^days - 1
        
        Args:
            days: Gün sayısı
            daily_rate: Günlük kazanç oranı (varsayılan %1)
            
        Returns:
            Toplam kazanç oranı
        """
        if daily_rate is None:
            daily_rate = self.daily_target_profit
            
        return (1 + daily_rate) ** days - 1
    
    def get_monthly_target_capital(self, month: int) -> float:
        """
        Aylık hedef sermaye hesaplama
        
        Args:
            month: Ay numarası (1 veya 2)
            
        Returns:
            Hedef sermaye miktarı
        """
        target_rate = self.monthly_targets.get(month, 0.348)
        return self.initial_capital * (1 + target_rate)
    
    def calculate_position_size(self, current_capital: float, risk_percentage: float = 0.02) -> float:
        """
        Position size hesaplama (sermayenin %2'si max risk)
        
        Args:
            current_capital: Mevcut sermaye
            risk_percentage: Risk yüzdesi (varsayılan %2)
            
        Returns:
            Position size miktarı
        """
        return current_capital * risk_percentage
    
    def record_trade(self, trade_type: str, symbol: str, amount: float, 
                    entry_price: float, exit_price: float = None, 
                    profit_loss: float = None) -> Dict:
        """
        Trade kaydı ve kazanç hesaplama
        
        Args:
            trade_type: 'BUY' veya 'SELL'
            symbol: İşlem yapılan sembol
            amount: İşlem miktarı
            entry_price: Giriş fiyatı
            exit_price: Çıkış fiyatı (opsiyonel)
            profit_loss: Kazanç/Zarar (opsiyonel)
            
        Returns:
            Trade bilgileri dictionary
        """
        trade = {
            'timestamp': datetime.now(),
            'type': trade_type,
            'symbol': symbol,
            'amount': amount,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'profit_loss': profit_loss or 0,
            'capital_after': self.current_capital
        }
        
        if profit_loss:
            self.current_capital += profit_loss
            trade['capital_after'] = self.current_capital
            
        self.trade_history.append(trade)
        return trade
    
    def get_daily_performance(self, date: datetime = None) -> Dict:
        """
        Günlük performans analizi
        
        Args:
            date: Analiz edilecek tarih (varsayılan bugün)
            
        Returns:
            Günlük performans bilgileri
        """
        if date is None:
            date = datetime.now().date()
            
        daily_trades = [
            trade for trade in self.trade_history
            if trade['timestamp'].date() == date
        ]
        
        total_profit = sum(trade['profit_loss'] for trade in daily_trades)
        profit_rate = total_profit / self.initial_capital if self.initial_capital > 0 else 0
        
        return {
            'date': date,
            'trades_count': len(daily_trades),
            'total_profit': total_profit,
            'profit_rate': profit_rate,
            'target_achieved': profit_rate >= self.daily_target_profit,
            'trades': daily_trades
        }
    
    def get_monthly_performance(self, month: int, year: int = None) -> Dict:
        """
        Aylık performans analizi
        
        Args:
            month: Ay (1-12)
            year: Yıl (varsayılan bu yıl)
            
        Returns:
            Aylık performans bilgileri
        """
        if year is None:
            year = datetime.now().year
            
        month_trades = [
            trade for trade in self.trade_history
            if trade['timestamp'].month == month and trade['timestamp'].year == year
        ]
        
        total_profit = sum(trade['profit_loss'] for trade in month_trades)
        profit_rate = total_profit / self.initial_capital if self.initial_capital > 0 else 0
        
        target_rate = self.monthly_targets.get(month, 0.348)
        
        return {
            'month': month,
            'year': year,
            'trades_count': len(month_trades),
            'total_profit': total_profit,
            'profit_rate': profit_rate,
            'target_rate': target_rate,
            'target_achieved': profit_rate >= target_rate,
            'performance_ratio': profit_rate / target_rate if target_rate > 0 else 0
        }
    
    def calculate_required_daily_profit(self, current_day: int, month: int) -> float:
        """
        Mevcut gün için gerekli günlük kazanç hesaplama
        
        Args:
            current_day: Ayın kaçıncı günü
            month: Ay numarası
            
        Returns:
            Gerekli günlük kazanç miktarı
        """
        target_rate = self.monthly_targets.get(month, 0.348)
        current_rate = (self.current_capital - self.initial_capital) / self.initial_capital
        
        # Kalan günler için hedef hesaplama
        days_in_month = 30 if month == 1 else 30  # Basitleştirilmiş
        remaining_days = days_in_month - current_day + 1
        
        if remaining_days <= 0:
            return 0
            
        required_remaining_profit = target_rate - current_rate
        daily_profit_needed = self.current_capital * (
            (1 + required_remaining_profit) ** (1/remaining_days) - 1
        )
        
        return daily_profit_needed
    
    def get_performance_summary(self) -> Dict:
        """
        Genel performans özeti
        
        Returns:
            Performans özeti bilgileri
        """
        if not self.trade_history:
            return {
                'total_trades': 0,
                'total_profit': 0,
                'total_profit_rate': 0,
                'current_capital': self.current_capital,
                'win_rate': 0,
                'average_profit_per_trade': 0
            }
        
        total_profit = sum(trade['profit_loss'] for trade in self.trade_history)
        winning_trades = [t for t in self.trade_history if t['profit_loss'] > 0]
        
        return {
            'total_trades': len(self.trade_history),
            'total_profit': total_profit,
            'total_profit_rate': total_profit / self.initial_capital,
            'current_capital': self.current_capital,
            'win_rate': len(winning_trades) / len(self.trade_history),
            'average_profit_per_trade': total_profit / len(self.trade_history),
            'best_trade': max(self.trade_history, key=lambda x: x['profit_loss']),
            'worst_trade': min(self.trade_history, key=lambda x: x['profit_loss'])
        }