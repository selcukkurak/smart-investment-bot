"""
Smart Investment Bot - Portfolio Manager
Manages multi-asset portfolio with real-time tracking and allocation
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class AssetType(Enum):
    CRYPTOCURRENCY = "crypto"
    STOCK = "stock"
    COMMODITY = "commodity"
    FOREX = "forex"


@dataclass
class Asset:
    """Represents a tradeable asset"""
    symbol: str
    asset_type: AssetType
    current_price: float
    quantity: float = 0.0
    avg_cost: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    @property
    def market_value(self) -> float:
        """Current market value of the asset"""
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        """Total cost basis of the asset"""
        return self.quantity * self.avg_cost
    
    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss"""
        return self.market_value - self.cost_basis
    
    @property
    def unrealized_pnl_percent(self) -> float:
        """Unrealized profit/loss percentage"""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100


class PortfolioManager:
    """
    Manages the trading portfolio across multiple asset classes
    """
    
    def __init__(self, initial_cash: float):
        self.initial_cash = initial_cash
        self.cash_balance = initial_cash
        self.assets: Dict[str, Asset] = {}
        self.transaction_history: List[Dict] = []
        self.daily_snapshots: List[Dict] = []
        
    def add_asset(self, symbol: str, asset_type: AssetType, 
                 current_price: float) -> Asset:
        """Add a new asset to track"""
        asset = Asset(
            symbol=symbol,
            asset_type=asset_type,
            current_price=current_price
        )
        self.assets[symbol] = asset
        return asset
    
    def update_asset_price(self, symbol: str, new_price: float) -> bool:
        """Update asset price"""
        if symbol in self.assets:
            self.assets[symbol].current_price = new_price
            self.assets[symbol].last_updated = datetime.now()
            return True
        return False
    
    def buy_asset(self, symbol: str, quantity: float, price: float,
                 commission: float = 0.0) -> bool:
        """
        Buy an asset and update portfolio
        """
        total_cost = (quantity * price) + commission
        
        # Check if we have enough cash
        if total_cost > self.cash_balance:
            return False
        
        # Update cash balance
        self.cash_balance -= total_cost
        
        # Update or create asset position
        if symbol in self.assets:
            asset = self.assets[symbol]
            # Calculate new average cost
            old_value = asset.quantity * asset.avg_cost
            new_value = quantity * price
            total_quantity = asset.quantity + quantity
            
            asset.avg_cost = (old_value + new_value) / total_quantity
            asset.quantity = total_quantity
            asset.current_price = price
        else:
            # Create new asset
            self.assets[symbol] = Asset(
                symbol=symbol,
                asset_type=AssetType.CRYPTOCURRENCY,  # Default, should be passed
                current_price=price,
                quantity=quantity,
                avg_cost=price
            )
        
        # Record transaction
        self.record_transaction('BUY', symbol, quantity, price, commission)
        return True
    
    def sell_asset(self, symbol: str, quantity: float, price: float,
                  commission: float = 0.0) -> bool:
        """
        Sell an asset and update portfolio
        """
        if symbol not in self.assets:
            return False
        
        asset = self.assets[symbol]
        if asset.quantity < quantity:
            return False
        
        # Calculate proceeds
        proceeds = (quantity * price) - commission
        
        # Update cash balance
        self.cash_balance += proceeds
        
        # Update asset position
        asset.quantity -= quantity
        asset.current_price = price
        
        # Remove asset if quantity is zero
        if asset.quantity == 0:
            del self.assets[symbol]
        
        # Record transaction
        self.record_transaction('SELL', symbol, quantity, price, commission)
        return True
    
    def record_transaction(self, action: str, symbol: str, quantity: float,
                         price: float, commission: float = 0.0):
        """Record a transaction in history"""
        transaction = {
            'timestamp': datetime.now(),
            'action': action,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'commission': commission,
            'total': quantity * price + commission if action == 'BUY' else quantity * price - commission
        }
        self.transaction_history.append(transaction)
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        assets_value = sum(asset.market_value for asset in self.assets.values())
        return self.cash_balance + assets_value
    
    def get_asset_allocation(self) -> Dict[str, float]:
        """Get asset allocation percentages"""
        total_value = self.get_portfolio_value()
        if total_value == 0:
            return {}
        
        allocation = {'CASH': (self.cash_balance / total_value) * 100}
        
        for symbol, asset in self.assets.items():
            allocation[symbol] = (asset.market_value / total_value) * 100
        
        return allocation
    
    def get_asset_type_allocation(self) -> Dict[str, float]:
        """Get allocation by asset type"""
        total_value = self.get_portfolio_value()
        if total_value == 0:
            return {}
        
        type_allocation = {'CASH': (self.cash_balance / total_value) * 100}
        
        for asset in self.assets.values():
            asset_type = asset.asset_type.value
            if asset_type not in type_allocation:
                type_allocation[asset_type] = 0
            type_allocation[asset_type] += (asset.market_value / total_value) * 100
        
        return type_allocation
    
    def get_unrealized_pnl(self) -> Dict[str, float]:
        """Get unrealized P&L for all positions"""
        return {
            symbol: asset.unrealized_pnl 
            for symbol, asset in self.assets.items()
        }
    
    def get_total_unrealized_pnl(self) -> float:
        """Get total unrealized P&L"""
        return sum(asset.unrealized_pnl for asset in self.assets.values())
    
    def get_realized_pnl(self, days: Optional[int] = None) -> float:
        """
        Calculate realized P&L from transactions
        """
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            transactions = [
                t for t in self.transaction_history 
                if t['timestamp'] >= cutoff_date
            ]
        else:
            transactions = self.transaction_history
        
        realized_pnl = 0.0
        positions = {}  # Track positions for P&L calculation
        
        for tx in transactions:
            symbol = tx['symbol']
            if symbol not in positions:
                positions[symbol] = {'quantity': 0, 'total_cost': 0}
            
            if tx['action'] == 'BUY':
                positions[symbol]['quantity'] += tx['quantity']
                positions[symbol]['total_cost'] += tx['total']
            elif tx['action'] == 'SELL':
                if positions[symbol]['quantity'] > 0:
                    # Calculate average cost for sold portion
                    avg_cost = positions[symbol]['total_cost'] / positions[symbol]['quantity']
                    # Calculate realized P&L
                    realized_pnl += (tx['price'] - avg_cost) * tx['quantity'] - tx['commission']
                    
                    # Update position
                    cost_reduction = avg_cost * tx['quantity']
                    positions[symbol]['quantity'] -= tx['quantity']
                    positions[symbol]['total_cost'] -= cost_reduction
        
        return realized_pnl
    
    def take_daily_snapshot(self) -> Dict:
        """Take a daily snapshot of portfolio performance"""
        snapshot = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now(),
            'cash_balance': self.cash_balance,
            'total_portfolio_value': self.get_portfolio_value(),
            'total_unrealized_pnl': self.get_total_unrealized_pnl(),
            'asset_allocation': self.get_asset_allocation(),
            'asset_type_allocation': self.get_asset_type_allocation(),
            'assets_snapshot': {
                symbol: {
                    'quantity': asset.quantity,
                    'current_price': asset.current_price,
                    'market_value': asset.market_value,
                    'avg_cost': asset.avg_cost,
                    'unrealized_pnl': asset.unrealized_pnl,
                    'unrealized_pnl_percent': asset.unrealized_pnl_percent
                }
                for symbol, asset in self.assets.items()
            }
        }
        
        self.daily_snapshots.append(snapshot)
        return snapshot
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive portfolio performance summary"""
        current_value = self.get_portfolio_value()
        total_return = current_value - self.initial_cash
        total_return_percent = (total_return / self.initial_cash) * 100
        
        unrealized_pnl = self.get_total_unrealized_pnl()
        realized_pnl = self.get_realized_pnl()
        
        return {
            'initial_cash': self.initial_cash,
            'current_cash': self.cash_balance,
            'current_portfolio_value': current_value,
            'total_return': total_return,
            'total_return_percent': total_return_percent,
            'unrealized_pnl': unrealized_pnl,
            'realized_pnl': realized_pnl,
            'total_pnl': unrealized_pnl + realized_pnl,
            'asset_count': len(self.assets),
            'cash_allocation_percent': (self.cash_balance / current_value) * 100 if current_value > 0 else 100,
            'invested_allocation_percent': ((current_value - self.cash_balance) / current_value) * 100 if current_value > 0 else 0,
            'top_performers': self.get_top_performers(),
            'worst_performers': self.get_worst_performers()
        }
    
    def get_top_performers(self, limit: int = 3) -> List[Dict]:
        """Get top performing assets"""
        performers = []
        for symbol, asset in self.assets.items():
            if asset.quantity > 0:
                performers.append({
                    'symbol': symbol,
                    'unrealized_pnl': asset.unrealized_pnl,
                    'unrealized_pnl_percent': asset.unrealized_pnl_percent,
                    'market_value': asset.market_value
                })
        
        performers.sort(key=lambda x: x['unrealized_pnl_percent'], reverse=True)
        return performers[:limit]
    
    def get_worst_performers(self, limit: int = 3) -> List[Dict]:
        """Get worst performing assets"""
        performers = []
        for symbol, asset in self.assets.items():
            if asset.quantity > 0:
                performers.append({
                    'symbol': symbol,
                    'unrealized_pnl': asset.unrealized_pnl,
                    'unrealized_pnl_percent': asset.unrealized_pnl_percent,
                    'market_value': asset.market_value
                })
        
        performers.sort(key=lambda x: x['unrealized_pnl_percent'])
        return performers[:limit]