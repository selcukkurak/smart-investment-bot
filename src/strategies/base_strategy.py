"""
Base Trading Strategy - Temel strateji sınıfı
Tüm trading stratejileri için ortak interface
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import logging


class SignalType(Enum):
    """Sinyal türleri"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class Signal:
    """Trading sinyali"""
    
    def __init__(self, symbol: str, signal_type: SignalType, 
                 confidence: float, price: float, timestamp: datetime = None):
        self.symbol = symbol
        self.signal_type = signal_type
        self.confidence = confidence  # 0.0 - 1.0
        self.price = price
        self.timestamp = timestamp or datetime.now()
        self.metadata = {}
        
    def add_metadata(self, key: str, value: Any) -> None:
        """Sinyal metadata ekleme"""
        self.metadata[key] = value
        
    def to_dict(self) -> Dict:
        """Dictionary formatına çevirme"""
        return {
            'symbol': self.symbol,
            'signal_type': self.signal_type.value,
            'confidence': self.confidence,
            'price': self.price,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class BaseStrategy(ABC):
    """
    Temel trading stratejisi sınıfı
    
    Tüm stratejiler bu sınıftan türeyecek
    """
    
    def __init__(self, name: str, timeframe: str = '1h'):
        """
        Base strategy başlatma
        
        Args:
            name: Strateji adı
            timeframe: Zaman dilimi
        """
        self.name = name
        self.timeframe = timeframe
        self.is_active = True
        self.min_confidence = 0.6  # Minimum sinyal güveni
        
        # Performance tracking
        self.signals_generated = 0
        self.signals_executed = 0
        self.successful_signals = 0
        self.total_profit = 0.0
        
        # Strategy parameters (override in subclasses)
        self.parameters = {}
        
        self.logger = logging.getLogger(f"Strategy.{self.name}")
        
    @abstractmethod
    async def analyze(self, symbol: str, historical_data: List[Dict],
                     current_price: float, **kwargs) -> Optional[Signal]:
        """
        Piyasa analizi ve sinyal üretme
        
        Args:
            symbol: Sembol adı
            historical_data: Geçmiş veri
            current_price: Güncel fiyat
            **kwargs: Ek parametreler
            
        Returns:
            Trading sinyali (None ise sinyal yok)
        """
        pass
    
    @abstractmethod
    def get_risk_parameters(self, signal: Signal) -> Dict:
        """
        Risk parametrelerini belirleme
        
        Args:
            signal: Trading sinyali
            
        Returns:
            Risk parametreleri (stop_loss, take_profit, position_size_pct)
        """
        pass
    
    def validate_signal(self, signal: Signal) -> bool:
        """
        Sinyal doğrulama
        
        Args:
            signal: Kontrol edilecek sinyal
            
        Returns:
            Sinyal geçerli mi
        """
        if not signal:
            return False
            
        # Minimum confidence kontrolü
        if signal.confidence < self.min_confidence:
            return False
            
        # Price validity kontrolü
        if signal.price <= 0:
            return False
            
        # Timestamp kontrolü (çok eski sinyaller geçersiz)
        time_diff = datetime.now() - signal.timestamp
        if time_diff.total_seconds() > 3600:  # 1 saat
            return False
            
        return True
    
    def update_performance(self, signal: Signal, executed: bool, 
                          profit: float = 0.0) -> None:
        """
        Performans güncelleme
        
        Args:
            signal: Çalıştırılan sinyal
            executed: Sinyal çalıştırıldı mı
            profit: Elde edilen kar/zarar
        """
        self.signals_generated += 1
        
        if executed:
            self.signals_executed += 1
            self.total_profit += profit
            
            if profit > 0:
                self.successful_signals += 1
                
        self.logger.info(
            f"Signal performance updated: {self.successful_signals}/{self.signals_executed} "
            f"successful (Total profit: ${self.total_profit:.2f})"
        )
    
    def get_performance_metrics(self) -> Dict:
        """
        Performans metrikleri
        
        Returns:
            Strateji performans bilgileri
        """
        win_rate = (
            self.successful_signals / self.signals_executed 
            if self.signals_executed > 0 else 0
        )
        
        execution_rate = (
            self.signals_executed / self.signals_generated
            if self.signals_generated > 0 else 0
        )
        
        avg_profit_per_signal = (
            self.total_profit / self.signals_executed
            if self.signals_executed > 0 else 0
        )
        
        return {
            'strategy_name': self.name,
            'signals_generated': self.signals_generated,
            'signals_executed': self.signals_executed,
            'successful_signals': self.successful_signals,
            'win_rate': win_rate,
            'execution_rate': execution_rate,
            'total_profit': self.total_profit,
            'average_profit_per_signal': avg_profit_per_signal,
            'is_active': self.is_active,
            'parameters': self.parameters
        }
    
    def set_parameter(self, key: str, value: Any) -> None:
        """Strateji parametresi ayarlama"""
        self.parameters[key] = value
        self.logger.info(f"Parameter updated: {key} = {value}")
    
    def enable(self) -> None:
        """Stratejiyi aktifleştirme"""
        self.is_active = True
        self.logger.info(f"Strategy {self.name} enabled")
    
    def disable(self) -> None:
        """Stratejiyi deaktifleştirme"""
        self.is_active = False
        self.logger.info(f"Strategy {self.name} disabled")
    
    def reset_performance(self) -> None:
        """Performans verilerini sıfırlama"""
        self.signals_generated = 0
        self.signals_executed = 0
        self.successful_signals = 0
        self.total_profit = 0.0
        self.logger.info(f"Performance data reset for {self.name}")
    
    def calculate_position_size(self, capital: float, risk_percentage: float = 0.02,
                              signal: Signal = None) -> float:
        """
        Position size hesaplama
        
        Args:
            capital: Mevcut sermaye
            risk_percentage: Risk yüzdesi
            signal: Trading sinyali
            
        Returns:
            Position size
        """
        base_size = capital * risk_percentage
        
        # Confidence bazlı ayarlama
        if signal and signal.confidence:
            confidence_multiplier = min(1.5, signal.confidence + 0.5)
            base_size *= confidence_multiplier
            
        return min(base_size, capital * 0.1)  # Max %10 risk
    
    def should_execute_signal(self, signal: Signal, current_positions: Dict,
                            portfolio_risk: float) -> Dict:
        """
        Sinyal çalıştırılmalı mı kontrolü
        
        Args:
            signal: Trading sinyali
            current_positions: Mevcut pozisyonlar
            portfolio_risk: Portföy riski
            
        Returns:
            Execution decision
        """
        if not self.is_active:
            return {
                'should_execute': False,
                'reason': 'Strategy is disabled'
            }
            
        if not self.validate_signal(signal):
            return {
                'should_execute': False,
                'reason': 'Signal validation failed'
            }
            
        # Pozisyon kontrolü
        if signal.symbol in current_positions:
            existing_position = current_positions[signal.symbol]
            
            # Aynı yönde pozisyon varsa skip
            if ((signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY] and 
                 existing_position.amount > 0) or
                (signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL] and
                 existing_position.amount < 0)):
                return {
                    'should_execute': False,
                    'reason': 'Already have position in same direction'
                }
        
        # Risk kontrolü
        if portfolio_risk > 0.15:  # %15'ten fazla risk
            return {
                'should_execute': False,
                'reason': 'Portfolio risk too high'
            }
            
        return {
            'should_execute': True,
            'reason': 'Signal approved for execution'
        }
    
    def get_strategy_info(self) -> Dict:
        """
        Strateji bilgileri
        
        Returns:
            Strateji detayları
        """
        return {
            'name': self.name,
            'timeframe': self.timeframe,
            'is_active': self.is_active,
            'min_confidence': self.min_confidence,
            'parameters': self.parameters,
            'performance': self.get_performance_metrics(),
            'description': self.__doc__ or f"{self.name} trading strategy"
        }