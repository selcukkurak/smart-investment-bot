"""
Risk Manager - Risk yönetimi ve pozisyon kontrolü
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np


class RiskLevel(Enum):
    """Risk seviyeleri"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class Position:
    """Pozisyon bilgileri"""
    symbol: str
    amount: float
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_amount: float = 0.0
    
    @property
    def unrealized_pnl(self) -> float:
        """Gerçekleşmemiş kar/zarar"""
        return (self.current_price - self.entry_price) * self.amount
    
    @property
    def unrealized_pnl_percentage(self) -> float:
        """Gerçekleşmemiş kar/zarar yüzdesi"""
        if self.entry_price == 0:
            return 0
        return (self.current_price - self.entry_price) / self.entry_price


class RiskManager:
    """
    Risk yönetimi sınıfı
    
    Özellikler:
    - Position sizing
    - Stop-loss ve take-profit hesaplama
    - Portföy risk analizi
    - Maksimum risk limitleri
    """
    
    def __init__(self, max_risk_per_trade: float = 0.02, 
                 max_portfolio_risk: float = 0.10,
                 max_correlation_exposure: float = 0.30):
        """
        Risk manager başlatma
        
        Args:
            max_risk_per_trade: Tek işlem için maksimum risk (%2)
            max_portfolio_risk: Toplam portföy riski (%10)
            max_correlation_exposure: Korelasyonlu varlıklara max exposure (%30)
        """
        self.max_risk_per_trade = max_risk_per_trade
        self.max_portfolio_risk = max_portfolio_risk
        self.max_correlation_exposure = max_correlation_exposure
        self.positions: Dict[str, Position] = {}
        self.risk_events: List[Dict] = []
        
    def calculate_position_size(self, capital: float, entry_price: float, 
                              stop_loss: float, risk_amount: float = None) -> float:
        """
        Position size hesaplama
        
        Args:
            capital: Mevcut sermaye
            entry_price: Giriş fiyatı
            stop_loss: Stop-loss seviyesi
            risk_amount: Risk edilecek miktar (varsayılan: sermayenin %2'si)
            
        Returns:
            Alınacak pozisyon büyüklüğü
        """
        if risk_amount is None:
            risk_amount = capital * self.max_risk_per_trade
            
        if entry_price <= 0 or stop_loss <= 0:
            return 0
            
        # Risk per unit hesaplama
        risk_per_unit = abs(entry_price - stop_loss)
        
        if risk_per_unit == 0:
            return 0
            
        # Position size = Risk miktarı / Birim başına risk
        position_size = risk_amount / risk_per_unit
        
        # Maksimum sermayenin %50'si kadar pozisyon alınabilir
        max_position_value = capital * 0.5
        max_position_size = max_position_value / entry_price
        
        return min(position_size, max_position_size)
    
    def calculate_stop_loss(self, entry_price: float, direction: str = 'long',
                          atr: float = None, risk_multiplier: float = 2.0) -> float:
        """
        Stop-loss seviyesi hesaplama
        
        Args:
            entry_price: Giriş fiyatı
            direction: 'long' veya 'short'
            atr: Average True Range (opsiyonel)
            risk_multiplier: Risk çarpanı
            
        Returns:
            Stop-loss fiyat seviyesi
        """
        if atr:
            # ATR bazlı stop-loss
            if direction.lower() == 'long':
                return entry_price - (atr * risk_multiplier)
            else:
                return entry_price + (atr * risk_multiplier)
        else:
            # Basit yüzde bazlı stop-loss (%2)
            if direction.lower() == 'long':
                return entry_price * (1 - 0.02)
            else:
                return entry_price * (1 + 0.02)
    
    def calculate_take_profit(self, entry_price: float, stop_loss: float,
                            direction: str = 'long', reward_ratio: float = 2.0) -> float:
        """
        Take-profit seviyesi hesaplama
        
        Args:
            entry_price: Giriş fiyatı
            stop_loss: Stop-loss seviyesi
            direction: 'long' veya 'short'
            reward_ratio: Risk/ödül oranı
            
        Returns:
            Take-profit fiyat seviyesi
        """
        risk_amount = abs(entry_price - stop_loss)
        reward_amount = risk_amount * reward_ratio
        
        if direction.lower() == 'long':
            return entry_price + reward_amount
        else:
            return entry_price - reward_amount
    
    def assess_portfolio_risk(self, capital: float) -> Dict:
        """
        Portföy risk değerlendirmesi
        
        Args:
            capital: Mevcut toplam sermaye
            
        Returns:
            Risk analizi sonuçları
        """
        if not self.positions:
            return {
                'total_exposure': 0,
                'total_risk': 0,
                'risk_ratio': 0,
                'risk_level': RiskLevel.LOW,
                'recommendations': ['Portfolio is empty - safe to start trading']
            }
        
        total_exposure = sum(
            pos.amount * pos.current_price for pos in self.positions.values()
        )
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_risk = sum(pos.risk_amount for pos in self.positions.values())
        
        exposure_ratio = total_exposure / capital if capital > 0 else 0
        risk_ratio = total_risk / capital if capital > 0 else 0
        
        # Risk seviyesi belirleme
        if risk_ratio <= 0.05:
            risk_level = RiskLevel.LOW
        elif risk_ratio <= 0.10:
            risk_level = RiskLevel.MEDIUM
        elif risk_ratio <= 0.20:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.EXTREME
            
        recommendations = self._generate_risk_recommendations(
            exposure_ratio, risk_ratio, risk_level
        )
        
        return {
            'total_exposure': total_exposure,
            'exposure_ratio': exposure_ratio,
            'total_risk': total_risk,
            'risk_ratio': risk_ratio,
            'unrealized_pnl': total_unrealized_pnl,
            'risk_level': risk_level,
            'recommendations': recommendations,
            'position_count': len(self.positions)
        }
    
    def _generate_risk_recommendations(self, exposure_ratio: float, 
                                     risk_ratio: float, risk_level: RiskLevel) -> List[str]:
        """Risk önerileri oluşturma"""
        recommendations = []
        
        if risk_level == RiskLevel.EXTREME:
            recommendations.append("🚨 EXTREME RISK: Consider closing some positions immediately")
            recommendations.append("📉 Portfolio risk exceeds safe limits")
            
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("⚠️ HIGH RISK: Monitor positions closely")
            recommendations.append("🎯 Consider taking profits on winning positions")
            
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("📊 MEDIUM RISK: Portfolio within acceptable limits")
            recommendations.append("🔍 Monitor for correlation risks")
            
        else:
            recommendations.append("✅ LOW RISK: Portfolio is well-managed")
            recommendations.append("📈 Good opportunity to add new positions")
            
        if exposure_ratio > 0.8:
            recommendations.append("💰 High exposure - consider keeping some cash reserves")
            
        if len(self.positions) > 10:
            recommendations.append("📊 Many open positions - ensure you can monitor all")
            
        return recommendations
    
    def check_correlation_risk(self, symbols: List[str], 
                             correlation_threshold: float = 0.7) -> Dict:
        """
        Korelasyon riski kontrolü
        
        Args:
            symbols: Kontrol edilecek semboller
            correlation_threshold: Korelasyon eşik değeri
            
        Returns:
            Korelasyon analizi sonuçları
        """
        # Bu basit implementasyonda sabit korelasyon değerleri kullanıyoruz
        # Gerçek uygulamada historical price data ile hesaplanabilir
        
        crypto_symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'DOT']
        stock_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        forex_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        
        correlations = {}
        high_correlation_groups = []
        
        # Kripto korelasyonları
        crypto_in_portfolio = [s for s in symbols if any(crypto in s for crypto in crypto_symbols)]
        if len(crypto_in_portfolio) > 1:
            correlations['crypto_group'] = 0.8
            high_correlation_groups.append(('crypto', crypto_in_portfolio))
            
        # Hisse senedi korelasyonları
        stocks_in_portfolio = [s for s in symbols if any(stock in s for stock in stock_symbols)]
        if len(stocks_in_portfolio) > 1:
            correlations['stock_group'] = 0.6
            high_correlation_groups.append(('stocks', stocks_in_portfolio))
        
        return {
            'correlations': correlations,
            'high_correlation_groups': high_correlation_groups,
            'correlation_risk': len(high_correlation_groups) > 0,
            'recommendations': self._generate_correlation_recommendations(high_correlation_groups)
        }
    
    def _generate_correlation_recommendations(self, groups: List[Tuple]) -> List[str]:
        """Korelasyon önerileri oluşturma"""
        recommendations = []
        
        for group_type, symbols in groups:
            if group_type == 'crypto':
                recommendations.append(
                    f"🔗 High crypto correlation detected: {', '.join(symbols)}"
                )
                recommendations.append("💡 Consider reducing exposure to correlated cryptos")
            elif group_type == 'stocks':
                recommendations.append(
                    f"🔗 High stock correlation detected: {', '.join(symbols)}"
                )
                recommendations.append("💡 Diversify across different sectors")
                
        return recommendations
    
    def add_position(self, symbol: str, amount: float, entry_price: float,
                    current_price: float, stop_loss: float = None,
                    take_profit: float = None) -> bool:
        """
        Yeni pozisyon ekleme
        
        Args:
            symbol: Sembol adı
            amount: Pozisyon miktarı
            entry_price: Giriş fiyatı
            current_price: Mevcut fiyat
            stop_loss: Stop-loss seviyesi
            take_profit: Take-profit seviyesi
            
        Returns:
            Pozisyon başarıyla eklendi mi
        """
        # Risk kontrolü
        risk_amount = abs(amount * (entry_price - (stop_loss or entry_price * 0.98)))
        
        position = Position(
            symbol=symbol,
            amount=amount,
            entry_price=entry_price,
            current_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=risk_amount
        )
        
        self.positions[symbol] = position
        return True
    
    def update_position_price(self, symbol: str, current_price: float) -> bool:
        """
        Pozisyon fiyatını güncelleme
        
        Args:
            symbol: Sembol adı
            current_price: Mevcut fiyat
            
        Returns:
            Güncelleme başarılı mı
        """
        if symbol in self.positions:
            self.positions[symbol].current_price = current_price
            return True
        return False
    
    def remove_position(self, symbol: str) -> bool:
        """
        Pozisyon silme
        
        Args:
            symbol: Sembol adı
            
        Returns:
            Silme başarılı mı
        """
        if symbol in self.positions:
            del self.positions[symbol]
            return True
        return False
    
    def check_stop_loss_triggers(self) -> List[str]:
        """
        Stop-loss tetiklenen pozisyonları kontrol etme
        
        Returns:
            Stop-loss tetiklenen sembollerin listesi
        """
        triggered_positions = []
        
        for symbol, position in self.positions.items():
            if position.stop_loss:
                # Long pozisyon için stop-loss kontrolü
                if position.amount > 0 and position.current_price <= position.stop_loss:
                    triggered_positions.append(symbol)
                # Short pozisyon için stop-loss kontrolü
                elif position.amount < 0 and position.current_price >= position.stop_loss:
                    triggered_positions.append(symbol)
                    
        return triggered_positions
    
    def check_take_profit_triggers(self) -> List[str]:
        """
        Take-profit tetiklenen pozisyonları kontrol etme
        
        Returns:
            Take-profit tetiklenen sembollerin listesi
        """
        triggered_positions = []
        
        for symbol, position in self.positions.items():
            if position.take_profit:
                # Long pozisyon için take-profit kontrolü
                if position.amount > 0 and position.current_price >= position.take_profit:
                    triggered_positions.append(symbol)
                # Short pozisyon için take-profit kontrolü
                elif position.amount < 0 and position.current_price <= position.take_profit:
                    triggered_positions.append(symbol)
                    
        return triggered_positions
    
    def calculate_portfolio_var(self, confidence_level: float = 0.95,
                              time_horizon: int = 1) -> float:
        """
        Value at Risk (VaR) hesaplama
        
        Args:
            confidence_level: Güven seviyesi (varsayılan %95)
            time_horizon: Zaman dilimi (gün)
            
        Returns:
            VaR değeri
        """
        if not self.positions:
            return 0
            
        # Basitleştirilmiş VaR hesaplama
        # Gerçek uygulamada historical volatility kullanılır
        
        portfolio_value = sum(
            abs(pos.amount * pos.current_price) for pos in self.positions.values()
        )
        
        # Varsayılan günlük volatilite %2
        daily_volatility = 0.02
        
        # Normal dağılım z-score
        z_score = 1.96 if confidence_level == 0.95 else 1.645  # %95 için 1.96
        
        var = portfolio_value * daily_volatility * z_score * (time_horizon ** 0.5)
        
        return var
    
    def validate_new_trade(self, symbol: str, amount: float, entry_price: float,
                          capital: float) -> Dict:
        """
        Yeni trade için risk doğrulama
        
        Args:
            symbol: Sembol adı
            amount: İşlem miktarı
            entry_price: Giriş fiyatı
            capital: Mevcut sermaye
            
        Returns:
            Doğrulama sonuçları
        """
        validation_result = {
            'approved': True,
            'warnings': [],
            'errors': [],
            'risk_metrics': {}
        }
        
        # Pozisyon değeri kontrolü
        position_value = abs(amount * entry_price)
        exposure_ratio = position_value / capital if capital > 0 else 0
        
        # Risk kontrolü
        if exposure_ratio > 0.2:  # %20'den fazla exposure
            validation_result['warnings'].append(
                f"High exposure: {exposure_ratio:.1%} of capital"
            )
            
        if exposure_ratio > 0.5:  # %50'den fazla exposure
            validation_result['errors'].append(
                f"Excessive exposure: {exposure_ratio:.1%} of capital"
            )
            validation_result['approved'] = False
            
        # Existing position kontrolü
        if symbol in self.positions:
            validation_result['warnings'].append(
                f"Existing position in {symbol} - consider position size"
            )
            
        # Portfolio risk kontrolü
        current_risk = self.assess_portfolio_risk(capital)
        new_risk_amount = capital * self.max_risk_per_trade
        total_risk_ratio = (current_risk['total_risk'] + new_risk_amount) / capital
        
        if total_risk_ratio > self.max_portfolio_risk:
            validation_result['errors'].append(
                f"Portfolio risk would exceed limit: {total_risk_ratio:.1%}"
            )
            validation_result['approved'] = False
            
        validation_result['risk_metrics'] = {
            'position_value': position_value,
            'exposure_ratio': exposure_ratio,
            'estimated_risk': new_risk_amount,
            'total_portfolio_risk_ratio': total_risk_ratio
        }
        
        return validation_result
    
    def get_risk_summary(self, capital: float) -> Dict:
        """
        Genel risk özeti
        
        Args:
            capital: Mevcut sermaye
            
        Returns:
            Risk özeti
        """
        portfolio_risk = self.assess_portfolio_risk(capital)
        var = self.calculate_portfolio_var()
        
        # Risk skorları
        risk_score = 0
        if portfolio_risk['risk_ratio'] > 0.15:
            risk_score += 3
        elif portfolio_risk['risk_ratio'] > 0.10:
            risk_score += 2
        elif portfolio_risk['risk_ratio'] > 0.05:
            risk_score += 1
            
        if len(self.positions) > 8:
            risk_score += 1
            
        risk_level = RiskLevel.LOW
        if risk_score >= 4:
            risk_level = RiskLevel.EXTREME
        elif risk_score >= 3:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 2:
            risk_level = RiskLevel.MEDIUM
            
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'portfolio_risk': portfolio_risk,
            'var_95': var,
            'active_positions': len(self.positions),
            'recommendations': portfolio_risk['recommendations']
        }