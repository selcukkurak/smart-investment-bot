"""
Database Models - SQLAlchemy modelleri
Bot verileri için database schema
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json


Base = declarative_base()


class Trade(Base):
    """Trading işlemleri tablosu"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    trade_type = Column(String(10), nullable=False)  # BUY, SELL
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    profit_loss = Column(Float, default=0.0)
    strategy = Column(String(50))
    
    # Risk management
    stop_loss = Column(Float)
    take_profit = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime)
    
    # Metadata
    exchange = Column(String(20))
    order_id = Column(String(100))
    notes = Column(Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'trade_type': self.trade_type,
            'amount': self.amount,
            'price': self.price,
            'total_value': self.total_value,
            'commission': self.commission,
            'profit_loss': self.profit_loss,
            'strategy': self.strategy,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'exchange': self.exchange,
            'order_id': self.order_id,
            'notes': self.notes
        }


class Portfolio(Base):
    """Portföy pozisyonları tablosu"""
    __tablename__ = 'portfolio'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, unique=True)
    asset_type = Column(String(20), nullable=False)  # crypto, stock, forex
    amount = Column(Float, nullable=False, default=0.0)
    average_cost = Column(Float, nullable=False, default=0.0)
    current_price = Column(Float, nullable=False, default=0.0)
    
    # Performance metrics
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    
    # Timestamps
    first_purchase = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Risk management
    stop_loss_level = Column(Float)
    take_profit_level = Column(Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'asset_type': self.asset_type,
            'amount': self.amount,
            'average_cost': self.average_cost,
            'current_price': self.current_price,
            'market_value': self.amount * self.current_price,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'first_purchase': self.first_purchase.isoformat() if self.first_purchase else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'stop_loss_level': self.stop_loss_level,
            'take_profit_level': self.take_profit_level
        }


class PerformanceMetrics(Base):
    """Günlük performans metrikleri"""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, unique=True)
    
    # Portfolio metrics
    total_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    invested_amount = Column(Float, nullable=False)
    
    # Performance
    daily_return = Column(Float, default=0.0)
    total_return = Column(Float, default=0.0)
    total_return_pct = Column(Float, default=0.0)
    
    # Trade metrics
    trades_count = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_commission = Column(Float, default=0.0)
    
    # Risk metrics
    max_drawdown = Column(Float, default=0.0)
    volatility = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    
    # Target achievement
    daily_target_met = Column(Boolean, default=False)
    monthly_target_progress = Column(Float, default=0.0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'total_value': self.total_value,
            'cash_balance': self.cash_balance,
            'invested_amount': self.invested_amount,
            'daily_return': self.daily_return,
            'total_return': self.total_return,
            'total_return_pct': self.total_return_pct,
            'trades_count': self.trades_count,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.winning_trades / self.trades_count if self.trades_count > 0 else 0,
            'total_commission': self.total_commission,
            'max_drawdown': self.max_drawdown,
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'daily_target_met': self.daily_target_met,
            'monthly_target_progress': self.monthly_target_progress
        }


class Signal(Base):
    """Trading sinyalleri tablosu"""
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    strategy = Column(String(50), nullable=False)
    signal_type = Column(String(20), nullable=False)  # BUY, SELL, HOLD
    confidence = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    
    # Technical data
    rsi = Column(Float)
    macd = Column(Float)
    volume_ratio = Column(Float)
    
    # Status
    executed = Column(Boolean, default=False)
    execution_price = Column(Float)
    profit_loss = Column(Float)
    
    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime)
    
    # Metadata (JSON)
    metadata = Column(Text)  # JSON string for additional data
    
    def set_metadata(self, data: dict):
        """Metadata ayarlama"""
        self.metadata = json.dumps(data)
    
    def get_metadata(self) -> dict:
        """Metadata alma"""
        try:
            return json.loads(self.metadata) if self.metadata else {}
        except json.JSONDecodeError:
            return {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'strategy': self.strategy,
            'signal_type': self.signal_type,
            'confidence': self.confidence,
            'price': self.price,
            'rsi': self.rsi,
            'macd': self.macd,
            'volume_ratio': self.volume_ratio,
            'executed': self.executed,
            'execution_price': self.execution_price,
            'profit_loss': self.profit_loss,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'metadata': self.get_metadata()
        }


class MarketData(Base):
    """Piyasa verileri cache tablosu"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    asset_type = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d
    
    # OHLCV data
    timestamp = Column(DateTime, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, default=0.0)
    
    # Technical indicators (calculated)
    rsi = Column(Float)
    macd_line = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    bb_upper = Column(Float)
    bb_middle = Column(Float)
    bb_lower = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'asset_type': self.asset_type,
            'timeframe': self.timeframe,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'open': self.open_price,
            'high': self.high_price,
            'low': self.low_price,
            'close': self.close_price,
            'volume': self.volume,
            'rsi': self.rsi,
            'macd_line': self.macd_line,
            'macd_signal': self.macd_signal,
            'macd_histogram': self.macd_histogram,
            'bb_upper': self.bb_upper,
            'bb_middle': self.bb_middle,
            'bb_lower': self.bb_lower,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class BotStatus(Base):
    """Bot durum tablosu"""
    __tablename__ = 'bot_status'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Bot state
    is_running = Column(Boolean, default=False)
    is_trading_enabled = Column(Boolean, default=True)
    trading_mode = Column(String(20), default='paper')
    
    # Performance
    total_value = Column(Float, default=0.0)
    total_return = Column(Float, default=0.0)
    daily_return = Column(Float, default=0.0)
    
    # Statistics
    active_positions = Column(Integer, default=0)
    daily_trades = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    # Risk
    portfolio_risk_level = Column(String(20), default='low')
    risk_score = Column(Float, default=0.0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'is_running': self.is_running,
            'is_trading_enabled': self.is_trading_enabled,
            'trading_mode': self.trading_mode,
            'total_value': self.total_value,
            'total_return': self.total_return,
            'daily_return': self.daily_return,
            'active_positions': self.active_positions,
            'daily_trades': self.daily_trades,
            'error_count': self.error_count,
            'portfolio_risk_level': self.portfolio_risk_level,
            'risk_score': self.risk_score
        }


class Alert(Base):
    """Uyarılar tablosu"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    alert_type = Column(String(50), nullable=False)  # RISK, SIGNAL, PROFIT, etc.
    symbol = Column(String(20))
    message = Column(Text, nullable=False)
    severity = Column(String(20), default='info')  # info, warning, error, critical
    
    # Status
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    
    # Data
    alert_data = Column(Text)  # JSON string
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime)
    dismissed_at = Column(DateTime)
    
    def set_data(self, data: dict):
        """Alert data ayarlama"""
        self.alert_data = json.dumps(data)
    
    def get_data(self) -> dict:
        """Alert data alma"""
        try:
            return json.loads(self.alert_data) if self.alert_data else {}
        except json.JSONDecodeError:
            return {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'symbol': self.symbol,
            'message': self.message,
            'severity': self.severity,
            'is_read': self.is_read,
            'is_dismissed': self.is_dismissed,
            'alert_data': self.get_data(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'dismissed_at': self.dismissed_at.isoformat() if self.dismissed_at else None
        }


class Configuration(Base):
    """Konfigürasyon tablosu"""
    __tablename__ = 'configuration'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(20), default='string')  # string, int, float, bool, json
    description = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_typed_value(self):
        """Type'a göre değer dönüşümü"""
        try:
            if self.value_type == 'int':
                return int(self.value)
            elif self.value_type == 'float':
                return float(self.value)
            elif self.value_type == 'bool':
                return self.value.lower() in ('true', '1', 'yes', 'on')
            elif self.value_type == 'json':
                return json.loads(self.value)
            else:
                return self.value
        except (ValueError, json.JSONDecodeError):
            return self.value
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.get_typed_value(),
            'value_type': self.value_type,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SentimentRecord(Base):
    """Sentiment analizi kayıtları"""
    __tablename__ = 'sentiment_records'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    sentiment_score = Column(Float, nullable=False)  # -1.0 to 1.0
    confidence = Column(Float, nullable=False)       # 0.0 to 1.0
    sources_count = Column(Integer, default=0)
    
    # Source breakdown
    news_sentiment = Column(Float)
    social_sentiment = Column(Float)
    market_sentiment = Column(Float)
    
    # Timestamp
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Raw data (optional)
    raw_data = Column(Text)  # JSON string
    
    def set_raw_data(self, data: dict):
        """Raw data ayarlama"""
        self.raw_data = json.dumps(data)
    
    def get_raw_data(self) -> dict:
        """Raw data alma"""
        try:
            return json.loads(self.raw_data) if self.raw_data else {}
        except json.JSONDecodeError:
            return {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'sentiment_score': self.sentiment_score,
            'confidence': self.confidence,
            'sources_count': self.sources_count,
            'news_sentiment': self.news_sentiment,
            'social_sentiment': self.social_sentiment,
            'market_sentiment': self.market_sentiment,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None,
            'raw_data': self.get_raw_data()
        }


class Backtest(Base):
    """Backtest sonuçları tablosu"""
    __tablename__ = 'backtests'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    strategy = Column(String(50), nullable=False)
    
    # Period
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Initial conditions
    initial_capital = Column(Float, nullable=False)
    
    # Results
    final_capital = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    total_return_pct = Column(Float, nullable=False)
    
    # Performance metrics
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    
    # Trade statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Configuration
    parameters = Column(Text)  # JSON string
    
    def set_parameters(self, params: dict):
        """Parameters ayarlama"""
        self.parameters = json.dumps(params)
    
    def get_parameters(self) -> dict:
        """Parameters alma"""
        try:
            return json.loads(self.parameters) if self.parameters else {}
        except json.JSONDecodeError:
            return {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'strategy': self.strategy,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'total_return': self.total_return,
            'total_return_pct': self.total_return_pct,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'win_rate': self.win_rate,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'parameters': self.get_parameters()
        }