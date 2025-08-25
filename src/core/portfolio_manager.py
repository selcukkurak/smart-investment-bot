"""
Portfolio Manager - Portföy yönetimi ve asset allocation
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd
import numpy as np


class AssetType(Enum):
    """Varlık türleri"""
    CRYPTO = "crypto"
    STOCK = "stock"
    FOREX = "forex"
    COMMODITY = "commodity"


@dataclass
class Asset:
    """Varlık bilgileri"""
    symbol: str
    asset_type: AssetType
    current_price: float
    amount: float = 0.0
    average_cost: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def market_value(self) -> float:
        """Piyasa değeri"""
        return self.amount * self.current_price
    
    @property
    def total_cost(self) -> float:
        """Toplam maliyet"""
        return self.amount * self.average_cost
    
    @property
    def unrealized_pnl(self) -> float:
        """Gerçekleşmemiş kar/zarar"""
        return self.market_value - self.total_cost
    
    @property
    def unrealized_pnl_percentage(self) -> float:
        """Gerçekleşmemiş kar/zarar yüzdesi"""
        if self.total_cost == 0:
            return 0
        return self.unrealized_pnl / self.total_cost


class PortfolioManager:
    """
    Portföy yönetimi sınıfı
    
    Özellikler:
    - Multi-asset portfolio yönetimi
    - Asset allocation
    - Rebalancing
    - Performance tracking
    - Diversification analysis
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        """
        Portfolio manager başlatma
        
        Args:
            initial_capital: Başlangıç sermayesi
        """
        self.initial_capital = initial_capital
        self.cash_balance = initial_capital
        self.assets: Dict[str, Asset] = {}
        self.trade_history: List[Dict] = []
        self.rebalance_history: List[Dict] = []
        
        # Hedef allocation (%)
        self.target_allocation = {
            AssetType.CRYPTO: 0.40,    # %40 kripto
            AssetType.STOCK: 0.35,     # %35 hisse
            AssetType.FOREX: 0.20,     # %20 forex
            AssetType.COMMODITY: 0.05  # %5 emtia
        }
        
    def add_asset(self, symbol: str, asset_type: AssetType, 
                  current_price: float) -> bool:
        """
        Portföye yeni varlık ekleme
        
        Args:
            symbol: Sembol adı
            asset_type: Varlık türü
            current_price: Mevcut fiyat
            
        Returns:
            Ekleme başarılı mı
        """
        if symbol not in self.assets:
            self.assets[symbol] = Asset(
                symbol=symbol,
                asset_type=asset_type,
                current_price=current_price
            )
            return True
        return False
    
    def buy_asset(self, symbol: str, amount: float, price: float) -> Dict:
        """
        Varlık satın alma
        
        Args:
            symbol: Sembol adı
            amount: Miktar
            price: Fiyat
            
        Returns:
            İşlem sonucu
        """
        total_cost = amount * price
        
        if total_cost > self.cash_balance:
            return {
                'success': False,
                'message': 'Insufficient cash balance',
                'required': total_cost,
                'available': self.cash_balance
            }
            
        if symbol not in self.assets:
            return {
                'success': False,
                'message': f'Asset {symbol} not found in portfolio'
            }
            
        asset = self.assets[symbol]
        
        # Average cost hesaplama
        total_amount = asset.amount + amount
        total_value = (asset.amount * asset.average_cost) + total_cost
        new_average_cost = total_value / total_amount if total_amount > 0 else price
        
        # Asset güncelleme
        asset.amount = total_amount
        asset.average_cost = new_average_cost
        asset.current_price = price
        asset.last_updated = datetime.now()
        
        # Cash balance güncelleme
        self.cash_balance -= total_cost
        
        # Trade history
        trade = {
            'timestamp': datetime.now(),
            'type': 'BUY',
            'symbol': symbol,
            'amount': amount,
            'price': price,
            'total_cost': total_cost,
            'cash_balance_after': self.cash_balance
        }
        self.trade_history.append(trade)
        
        return {
            'success': True,
            'trade': trade,
            'new_amount': asset.amount,
            'new_average_cost': asset.average_cost
        }
    
    def sell_asset(self, symbol: str, amount: float, price: float) -> Dict:
        """
        Varlık satma
        
        Args:
            symbol: Sembol adı
            amount: Miktar
            price: Fiyat
            
        Returns:
            İşlem sonucu
        """
        if symbol not in self.assets:
            return {
                'success': False,
                'message': f'Asset {symbol} not found in portfolio'
            }
            
        asset = self.assets[symbol]
        
        if amount > asset.amount:
            return {
                'success': False,
                'message': 'Insufficient asset amount',
                'requested': amount,
                'available': asset.amount
            }
            
        total_proceeds = amount * price
        cost_basis = amount * asset.average_cost
        realized_pnl = total_proceeds - cost_basis
        
        # Asset güncelleme
        asset.amount -= amount
        asset.current_price = price
        asset.last_updated = datetime.now()
        
        # Cash balance güncelleme
        self.cash_balance += total_proceeds
        
        # Trade history
        trade = {
            'timestamp': datetime.now(),
            'type': 'SELL',
            'symbol': symbol,
            'amount': amount,
            'price': price,
            'total_proceeds': total_proceeds,
            'cost_basis': cost_basis,
            'realized_pnl': realized_pnl,
            'cash_balance_after': self.cash_balance
        }
        self.trade_history.append(trade)
        
        return {
            'success': True,
            'trade': trade,
            'realized_pnl': realized_pnl,
            'remaining_amount': asset.amount
        }
    
    def update_prices(self, price_updates: Dict[str, float]) -> int:
        """
        Fiyatları toplu güncelleme
        
        Args:
            price_updates: {symbol: new_price} dictionary
            
        Returns:
            Güncellenen asset sayısı
        """
        updated_count = 0
        
        for symbol, new_price in price_updates.items():
            if symbol in self.assets:
                self.assets[symbol].current_price = new_price
                self.assets[symbol].last_updated = datetime.now()
                updated_count += 1
                
        return updated_count
    
    def get_portfolio_value(self) -> float:
        """
        Toplam portföy değeri
        
        Returns:
            Toplam portföy değeri (cash + assets)
        """
        assets_value = sum(asset.market_value for asset in self.assets.values())
        return self.cash_balance + assets_value
    
    def get_asset_allocation(self) -> Dict[AssetType, Dict]:
        """
        Varlık dağılımı analizi
        
        Returns:
            Asset type bazında dağılım
        """
        total_value = self.get_portfolio_value()
        allocation = {}
        
        for asset_type in AssetType:
            type_assets = [a for a in self.assets.values() if a.asset_type == asset_type]
            type_value = sum(asset.market_value for asset in type_assets)
            
            allocation[asset_type] = {
                'value': type_value,
                'percentage': type_value / total_value if total_value > 0 else 0,
                'target_percentage': self.target_allocation.get(asset_type, 0),
                'assets': [asset.symbol for asset in type_assets],
                'count': len(type_assets)
            }
            
        # Cash allocation
        allocation['CASH'] = {
            'value': self.cash_balance,
            'percentage': self.cash_balance / total_value if total_value > 0 else 0,
            'target_percentage': 0.05  # %5 cash target
        }
        
        return allocation
    
    def calculate_rebalancing_needs(self) -> Dict:
        """
        Rebalancing ihtiyacı hesaplama
        
        Returns:
            Rebalancing önerileri
        """
        allocation = self.get_asset_allocation()
        total_value = self.get_portfolio_value()
        rebalancing_actions = []
        
        for asset_type, data in allocation.items():
            if asset_type == 'CASH':
                continue
                
            current_pct = data['percentage']
            target_pct = data['target_percentage']
            difference = current_pct - target_pct
            
            # %5'ten fazla sapma varsa rebalancing öner
            if abs(difference) > 0.05:
                action = 'REDUCE' if difference > 0 else 'INCREASE'
                target_value = total_value * target_pct
                current_value = data['value']
                adjustment_amount = abs(target_value - current_value)
                
                rebalancing_actions.append({
                    'asset_type': asset_type,
                    'action': action,
                    'current_percentage': current_pct,
                    'target_percentage': target_pct,
                    'difference': difference,
                    'adjustment_amount': adjustment_amount,
                    'priority': abs(difference)  # Sapma miktarına göre öncelik
                })
        
        # Öncelik sırasına göre sırala
        rebalancing_actions.sort(key=lambda x: x['priority'], reverse=True)
        
        return {
            'needs_rebalancing': len(rebalancing_actions) > 0,
            'actions': rebalancing_actions,
            'total_value': total_value,
            'current_allocation': allocation
        }
    
    def get_performance_metrics(self) -> Dict:
        """
        Performans metrikleri
        
        Returns:
            Performans analizi
        """
        current_value = self.get_portfolio_value()
        total_return = current_value - self.initial_capital
        total_return_pct = total_return / self.initial_capital if self.initial_capital > 0 else 0
        
        # Asset bazında performans
        asset_performance = {}
        for symbol, asset in self.assets.items():
            if asset.amount > 0:
                asset_performance[symbol] = {
                    'unrealized_pnl': asset.unrealized_pnl,
                    'unrealized_pnl_pct': asset.unrealized_pnl_percentage,
                    'market_value': asset.market_value,
                    'weight': asset.market_value / current_value if current_value > 0 else 0
                }
        
        # Trade analizi
        realized_trades = [t for t in self.trade_history if 'realized_pnl' in t]
        total_realized_pnl = sum(t['realized_pnl'] for t in realized_trades)
        winning_trades = [t for t in realized_trades if t['realized_pnl'] > 0]
        
        return {
            'total_value': current_value,
            'total_return': total_return,
            'total_return_percentage': total_return_pct,
            'cash_balance': self.cash_balance,
            'cash_percentage': self.cash_balance / current_value if current_value > 0 else 0,
            'realized_pnl': total_realized_pnl,
            'unrealized_pnl': sum(asset.unrealized_pnl for asset in self.assets.values()),
            'asset_performance': asset_performance,
            'trade_statistics': {
                'total_trades': len(realized_trades),
                'winning_trades': len(winning_trades),
                'win_rate': len(winning_trades) / len(realized_trades) if realized_trades else 0,
                'average_trade_pnl': total_realized_pnl / len(realized_trades) if realized_trades else 0
            }
        }
    
    def get_diversification_score(self) -> Dict:
        """
        Diversifikasyon skoru hesaplama
        
        Returns:
            Diversifikasyon analizi
        """
        if not self.assets:
            return {
                'score': 0,
                'level': 'No assets',
                'recommendations': ['Add assets to portfolio']
            }
            
        allocation = self.get_asset_allocation()
        total_value = self.get_portfolio_value()
        
        # Herfindahl Index hesaplama (konsantrasyon ölçümü)
        weights = []
        for asset in self.assets.values():
            if asset.amount > 0:
                weight = asset.market_value / total_value
                weights.append(weight)
                
        if not weights:
            return {
                'score': 0,
                'level': 'No positions',
                'recommendations': ['Open positions in different assets']
            }
            
        herfindahl_index = sum(w**2 for w in weights)
        
        # Diversifikasyon skoru (0-100)
        # Düşük HI = Yüksek diversifikasyon
        diversification_score = max(0, 100 * (1 - herfindahl_index))
        
        # Asset type diversifikasyonu
        active_types = len([at for at, data in allocation.items() 
                          if at != 'CASH' and data['value'] > 0])
        
        # Skor ayarlama
        type_diversity_bonus = min(20, active_types * 5)
        final_score = min(100, diversification_score + type_diversity_bonus)
        
        # Level belirleme
        if final_score >= 80:
            level = 'Excellent'
        elif final_score >= 60:
            level = 'Good'
        elif final_score >= 40:
            level = 'Fair'
        else:
            level = 'Poor'
            
        recommendations = self._generate_diversification_recommendations(
            allocation, active_types, final_score
        )
        
        return {
            'score': final_score,
            'level': level,
            'herfindahl_index': herfindahl_index,
            'active_asset_types': active_types,
            'asset_count': len([a for a in self.assets.values() if a.amount > 0]),
            'recommendations': recommendations
        }
    
    def _generate_diversification_recommendations(self, allocation: Dict, 
                                                active_types: int, score: float) -> List[str]:
        """Diversifikasyon önerileri oluşturma"""
        recommendations = []
        
        if score < 40:
            recommendations.append("🚨 Poor diversification - high concentration risk")
            
        if active_types < 2:
            recommendations.append("📊 Add assets from different asset classes")
            
        # Asset type bazında öneriler
        for asset_type, data in allocation.items():
            if asset_type == 'CASH':
                continue
                
            current_pct = data['percentage']
            target_pct = data['target_percentage']
            
            if current_pct > target_pct + 0.1:  # %10 fazla
                recommendations.append(
                    f"📉 Reduce {asset_type.value} exposure ({current_pct:.1%} vs target {target_pct:.1%})"
                )
            elif current_pct < target_pct - 0.1:  # %10 az
                recommendations.append(
                    f"📈 Increase {asset_type.value} exposure ({current_pct:.1%} vs target {target_pct:.1%})"
                )
                
        return recommendations
    
    def suggest_rebalancing(self) -> Dict:
        """
        Rebalancing önerileri
        
        Returns:
            Rebalancing planı
        """
        rebalancing_needs = self.calculate_rebalancing_needs()
        
        if not rebalancing_needs['needs_rebalancing']:
            return {
                'needs_rebalancing': False,
                'message': 'Portfolio is well balanced'
            }
            
        total_value = self.get_portfolio_value()
        actions = []
        
        for action in rebalancing_needs['actions']:
            asset_type = action['asset_type']
            target_value = total_value * action['target_percentage']
            current_value = action['current_percentage'] * total_value
            
            if action['action'] == 'REDUCE':
                # Satış önerisi
                excess_value = current_value - target_value
                type_assets = [a for a in self.assets.values() 
                             if a.asset_type == asset_type and a.amount > 0]
                
                for asset in type_assets:
                    if excess_value <= 0:
                        break
                        
                    # En karlı asset'ten sat
                    if asset.unrealized_pnl_percentage > 0:
                        sell_value = min(excess_value, asset.market_value * 0.5)
                        sell_amount = sell_value / asset.current_price
                        
                        actions.append({
                            'action': 'SELL',
                            'symbol': asset.symbol,
                            'amount': sell_amount,
                            'estimated_proceeds': sell_value,
                            'reason': f'Reduce {asset_type.value} allocation'
                        })
                        
                        excess_value -= sell_value
                        
            else:  # INCREASE
                # Satın alma önerisi
                needed_value = target_value - current_value
                available_cash = min(self.cash_balance, needed_value)
                
                if available_cash > 100:  # En az $100 yatırım
                    actions.append({
                        'action': 'BUY',
                        'asset_type': asset_type.value,
                        'amount': available_cash,
                        'reason': f'Increase {asset_type.value} allocation'
                    })
        
        return {
            'needs_rebalancing': True,
            'actions': actions,
            'estimated_transactions': len(actions),
            'total_value': total_value
        }
    
    def get_top_performers(self, limit: int = 5) -> List[Dict]:
        """
        En iyi performans gösteren varlıklar
        
        Args:
            limit: Sonuç limiti
            
        Returns:
            En iyi performans listesi
        """
        performers = []
        
        for asset in self.assets.values():
            if asset.amount > 0:
                performers.append({
                    'symbol': asset.symbol,
                    'asset_type': asset.asset_type.value,
                    'unrealized_pnl': asset.unrealized_pnl,
                    'unrealized_pnl_pct': asset.unrealized_pnl_percentage,
                    'market_value': asset.market_value,
                    'amount': asset.amount
                })
        
        # Yüzde bazında sırala
        performers.sort(key=lambda x: x['unrealized_pnl_pct'], reverse=True)
        
        return performers[:limit]
    
    def get_portfolio_summary(self) -> Dict:
        """
        Portföy özeti
        
        Returns:
            Genel portföy bilgileri
        """
        performance = self.get_performance_metrics()
        allocation = self.get_asset_allocation()
        diversification = self.get_diversification_score()
        top_performers = self.get_top_performers(3)
        
        return {
            'timestamp': datetime.now(),
            'total_value': performance['total_value'],
            'total_return': performance['total_return'],
            'total_return_percentage': performance['total_return_percentage'],
            'cash_balance': self.cash_balance,
            'active_positions': len([a for a in self.assets.values() if a.amount > 0]),
            'asset_allocation': allocation,
            'diversification': diversification,
            'top_performers': top_performers,
            'recent_trades': self.trade_history[-5:] if self.trade_history else []
        }
    
    def export_portfolio_data(self) -> pd.DataFrame:
        """
        Portföy verilerini DataFrame olarak export etme
        
        Returns:
            Portfolio DataFrame
        """
        data = []
        
        for asset in self.assets.values():
            if asset.amount > 0:
                data.append({
                    'Symbol': asset.symbol,
                    'Asset Type': asset.asset_type.value,
                    'Amount': asset.amount,
                    'Current Price': asset.current_price,
                    'Average Cost': asset.average_cost,
                    'Market Value': asset.market_value,
                    'Total Cost': asset.total_cost,
                    'Unrealized PnL': asset.unrealized_pnl,
                    'Unrealized PnL %': asset.unrealized_pnl_percentage,
                    'Last Updated': asset.last_updated
                })
        
        return pd.DataFrame(data)
    
    def reset_portfolio(self, new_capital: float = None) -> bool:
        """
        Portföyü sıfırlama
        
        Args:
            new_capital: Yeni başlangıç sermayesi
            
        Returns:
            Sıfırlama başarılı mı
        """
        if new_capital:
            self.initial_capital = new_capital
            self.cash_balance = new_capital
        else:
            self.cash_balance = self.initial_capital
            
        self.assets.clear()
        self.trade_history.clear()
        self.rebalance_history.clear()
        
        return True