"""
Smart Investment Bot - Database Models
SQLAlchemy models for storing trading data
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from typing import Dict, Any

Base = declarative_base()


class TradingSession(Base):
    """Trading session model"""
    __tablename__ = 'trading_sessions'
    
    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime)
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float)
    total_return = Column(Float)
    trades_count = Column(Integer, default=0)
    targets_met = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    trades = relationship("Trade", back_populates="session")
    daily_performances = relationship("DailyPerformance", back_populates="session")


class Trade(Base):
    """Individual trade model"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('trading_sessions.id'))
    symbol = Column(String(20), nullable=False)
    asset_type = Column(String(20), nullable=False)  # crypto, stock, commodity, forex
    action = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    total_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    strategy_used = Column(String(50))
    signal_confidence = Column(Float)
    notes = Column(Text)
    
    # Relationships
    session = relationship("TradingSession", back_populates="trades")


class Position(Base):
    """Active position model"""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('trading_sessions.id'))
    symbol = Column(String(20), nullable=False)
    position_type = Column(String(10), nullable=False)  # long, short
    entry_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    entry_time = Column(DateTime, default=datetime.now)
    exit_time = Column(DateTime)
    exit_price = Column(Float)
    pnl = Column(Float)
    exit_reason = Column(String(100))
    status = Column(String(20), default='open')  # open, closed


class DailyPerformance(Base):
    """Daily performance tracking"""
    __tablename__ = 'daily_performance'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('trading_sessions.id'))
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    opening_balance = Column(Float, nullable=False)
    closing_balance = Column(Float, nullable=False)
    daily_return = Column(Float, nullable=False)
    daily_return_rate = Column(Float, nullable=False)
    target_amount = Column(Float, nullable=False)
    target_rate = Column(Float, nullable=False)
    target_met = Column(Boolean, nullable=False)
    trades_count = Column(Integer, default=0)
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    
    # Relationships
    session = relationship("TradingSession", back_populates="daily_performances")


class MarketData(Base):
    """Market data cache"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    asset_type = Column(String(20), nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float)
    change_24h = Column(Float)
    volatility = Column(Float)
    timestamp = Column(DateTime, default=datetime.now)
    source = Column(String(50))  # yahoo, binance, etc.


class TechnicalIndicator(Base):
    """Technical indicators cache"""
    __tablename__ = 'technical_indicators'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 1h, etc.
    rsi = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    ema_12 = Column(Float)
    ema_26 = Column(Float)
    bb_upper = Column(Float)
    bb_middle = Column(Float)
    bb_lower = Column(Float)
    volume_ratio = Column(Float)
    timestamp = Column(DateTime, default=datetime.now)


class DatabaseManager:
    """
    Database manager for the Smart Investment Bot
    """
    
    def __init__(self, database_url: str = "sqlite:///smart_bot.db"):
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def create_trading_session(self, initial_capital: float) -> int:
        """Create new trading session"""
        session = self.get_session()
        try:
            trading_session = TradingSession(initial_capital=initial_capital)
            session.add(trading_session)
            session.commit()
            session_id = trading_session.id
            session.close()
            return session_id
        except Exception as e:
            session.rollback()
            session.close()
            raise e
    
    def save_trade(self, trade_data: Dict[str, Any]) -> bool:
        """Save trade to database"""
        session = self.get_session()
        try:
            trade = Trade(**trade_data)
            session.add(trade)
            session.commit()
            session.close()
            return True
        except Exception as e:
            session.rollback()
            session.close()
            print(f"Error saving trade: {e}")
            return False
    
    def save_daily_performance(self, performance_data: Dict[str, Any]) -> bool:
        """Save daily performance data"""
        session = self.get_session()
        try:
            daily_perf = DailyPerformance(**performance_data)
            session.add(daily_perf)
            session.commit()
            session.close()
            return True
        except Exception as e:
            session.rollback()
            session.close()
            print(f"Error saving daily performance: {e}")
            return False
    
    def get_trading_history(self, session_id: int, days: int = 30) -> List[Dict]:
        """Get trading history for analysis"""
        session = self.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            trades = session.query(Trade).filter(
                Trade.session_id == session_id,
                Trade.timestamp >= cutoff_date
            ).all()
            
            result = []
            for trade in trades:
                result.append({
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'action': trade.action,
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'total_value': trade.total_value,
                    'timestamp': trade.timestamp,
                    'strategy_used': trade.strategy_used
                })
            
            session.close()
            return result
        except Exception as e:
            session.close()
            print(f"Error getting trading history: {e}")
            return []
    
    def get_performance_metrics(self, session_id: int) -> Dict[str, Any]:
        """Get performance metrics"""
        session = self.get_session()
        try:
            # Get session info
            trading_session = session.query(TradingSession).filter(
                TradingSession.id == session_id
            ).first()
            
            if not trading_session:
                return {}
            
            # Get daily performances
            daily_perfs = session.query(DailyPerformance).filter(
                DailyPerformance.session_id == session_id
            ).all()
            
            # Calculate metrics
            total_days = len(daily_perfs)
            targets_met = sum(1 for dp in daily_perfs if dp.target_met)
            total_trades = trading_session.trades_count
            
            metrics = {
                'session_id': session_id,
                'start_time': trading_session.start_time,
                'initial_capital': trading_session.initial_capital,
                'current_capital': trading_session.final_capital or trading_session.initial_capital,
                'total_days': total_days,
                'targets_met': targets_met,
                'target_success_rate': targets_met / total_days if total_days > 0 else 0,
                'total_trades': total_trades,
                'daily_performances': [
                    {
                        'date': dp.date,
                        'return_rate': dp.daily_return_rate,
                        'target_met': dp.target_met,
                        'trades_count': dp.trades_count
                    }
                    for dp in daily_perfs[-7:]  # Last 7 days
                ]
            }
            
            session.close()
            return metrics
            
        except Exception as e:
            session.close()
            print(f"Error getting performance metrics: {e}")
            return {}