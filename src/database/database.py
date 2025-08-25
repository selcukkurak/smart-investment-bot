"""
Database Connection and Operations
SQLAlchemy ile database yönetimi
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, func
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import os

from .models import (
    Base, Trade, Portfolio, PerformanceMetrics, Signal,
    MarketData, BotStatus, Alert, Configuration, SentimentRecord, Backtest
)


class DatabaseManager:
    """
    Database yönetim sınıfı
    
    Özellikler:
    - Async SQLAlchemy operations
    - Connection pooling
    - Transaction management
    - Data CRUD operations
    - Performance queries
    """
    
    def __init__(self, database_url: str = None):
        """
        Database manager başlatma
        
        Args:
            database_url: Database URL (varsayılan SQLite)
        """
        if database_url is None:
            # Default SQLite database
            db_path = os.path.join(os.getcwd(), 'smart_investment_bot.db')
            database_url = f"sqlite+aiosqlite:///{db_path}"
            
        self.database_url = database_url
        self.engine = None
        self.async_session = None
        self.logger = logging.getLogger('DatabaseManager')
        
    async def initialize(self) -> bool:
        """
        Database bağlantısını başlatma
        
        Returns:
            Başlatma başarılı mı
        """
        try:
            # Create async engine
            self.engine = create_async_engine(
                self.database_url,
                echo=False,  # SQL query logging
                future=True,
                pool_pre_ping=True
            )
            
            # Create session factory
            self.async_session = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
            self.logger.info("✅ Database initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {str(e)}")
            return False
    
    async def close(self) -> None:
        """Database bağlantısını kapatma"""
        if self.engine:
            await self.engine.dispose()
            self.logger.info("Database connection closed")
    
    # Trade operations
    async def save_trade(self, trade_data: Dict) -> Optional[int]:
        """
        Trade kaydetme
        
        Args:
            trade_data: Trade bilgileri
            
        Returns:
            Trade ID (None ise hata)
        """
        try:
            async with self.async_session() as session:
                trade = Trade(
                    symbol=trade_data['symbol'],
                    trade_type=trade_data['trade_type'],
                    amount=trade_data['amount'],
                    price=trade_data['price'],
                    total_value=trade_data['total_value'],
                    commission=trade_data.get('commission', 0.0),
                    profit_loss=trade_data.get('profit_loss', 0.0),
                    strategy=trade_data.get('strategy'),
                    stop_loss=trade_data.get('stop_loss'),
                    take_profit=trade_data.get('take_profit'),
                    executed_at=trade_data.get('executed_at', datetime.utcnow()),
                    exchange=trade_data.get('exchange'),
                    order_id=trade_data.get('order_id'),
                    notes=trade_data.get('notes')
                )
                
                session.add(trade)
                await session.commit()
                await session.refresh(trade)
                
                return trade.id
                
        except Exception as e:
            self.logger.error(f"Error saving trade: {str(e)}")
            return None
    
    async def get_trades(self, symbol: str = None, limit: int = 100,
                        start_date: datetime = None) -> List[Dict]:
        """
        Trade'leri alma
        
        Args:
            symbol: Sembol filtresi
            limit: Sonuç limiti
            start_date: Başlangıç tarihi
            
        Returns:
            Trade listesi
        """
        try:
            async with self.async_session() as session:
                query = select(Trade).order_by(Trade.created_at.desc())
                
                if symbol:
                    query = query.where(Trade.symbol == symbol)
                    
                if start_date:
                    query = query.where(Trade.created_at >= start_date)
                    
                query = query.limit(limit)
                
                result = await session.execute(query)
                trades = result.scalars().all()
                
                return [trade.to_dict() for trade in trades]
                
        except Exception as e:
            self.logger.error(f"Error getting trades: {str(e)}")
            return []
    
    # Portfolio operations
    async def update_portfolio_position(self, position_data: Dict) -> bool:
        """
        Portfolio pozisyonu güncelleme
        
        Args:
            position_data: Pozisyon bilgileri
            
        Returns:
            Güncelleme başarılı mı
        """
        try:
            async with self.async_session() as session:
                # Existing position kontrolü
                result = await session.execute(
                    select(Portfolio).where(Portfolio.symbol == position_data['symbol'])
                )
                position = result.scalar_one_or_none()
                
                if position:
                    # Update existing
                    position.amount = position_data['amount']
                    position.average_cost = position_data['average_cost']
                    position.current_price = position_data['current_price']
                    position.unrealized_pnl = position_data.get('unrealized_pnl', 0.0)
                    position.last_updated = datetime.utcnow()
                else:
                    # Create new
                    position = Portfolio(
                        symbol=position_data['symbol'],
                        asset_type=position_data['asset_type'],
                        amount=position_data['amount'],
                        average_cost=position_data['average_cost'],
                        current_price=position_data['current_price'],
                        unrealized_pnl=position_data.get('unrealized_pnl', 0.0),
                        first_purchase=datetime.utcnow()
                    )
                    session.add(position)
                
                await session.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating portfolio position: {str(e)}")
            return False
    
    async def get_portfolio_positions(self) -> List[Dict]:
        """
        Aktif portföy pozisyonları
        
        Returns:
            Pozisyon listesi
        """
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(Portfolio).where(Portfolio.amount > 0)
                )
                positions = result.scalars().all()
                
                return [position.to_dict() for position in positions]
                
        except Exception as e:
            self.logger.error(f"Error getting portfolio positions: {str(e)}")
            return []
    
    # Performance operations
    async def save_daily_performance(self, performance_data: Dict) -> bool:
        """
        Günlük performans kaydetme
        
        Args:
            performance_data: Performans bilgileri
            
        Returns:
            Kaydetme başarılı mı
        """
        try:
            async with self.async_session() as session:
                # Check if record exists for today
                today = datetime.now().date()
                result = await session.execute(
                    select(PerformanceMetrics).where(
                        func.date(PerformanceMetrics.date) == today
                    )
                )
                performance = result.scalar_one_or_none()
                
                if performance:
                    # Update existing
                    for key, value in performance_data.items():
                        if hasattr(performance, key):
                            setattr(performance, key, value)
                else:
                    # Create new
                    performance = PerformanceMetrics(
                        date=datetime.now(),
                        **performance_data
                    )
                    session.add(performance)
                
                await session.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error saving daily performance: {str(e)}")
            return False
    
    async def get_performance_history(self, days: int = 30) -> List[Dict]:
        """
        Performans geçmişi
        
        Args:
            days: Gün sayısı
            
        Returns:
            Performans geçmişi
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            async with self.async_session() as session:
                result = await session.execute(
                    select(PerformanceMetrics)
                    .where(PerformanceMetrics.date >= start_date)
                    .order_by(PerformanceMetrics.date.desc())
                )
                performance_records = result.scalars().all()
                
                return [record.to_dict() for record in performance_records]
                
        except Exception as e:
            self.logger.error(f"Error getting performance history: {str(e)}")
            return []
    
    # Signal operations
    async def save_signal(self, signal_data: Dict) -> Optional[int]:
        """
        Trading sinyali kaydetme
        
        Args:
            signal_data: Sinyal bilgileri
            
        Returns:
            Signal ID
        """
        try:
            async with self.async_session() as session:
                signal = Signal(
                    symbol=signal_data['symbol'],
                    strategy=signal_data['strategy'],
                    signal_type=signal_data['signal_type'],
                    confidence=signal_data['confidence'],
                    price=signal_data['price'],
                    rsi=signal_data.get('rsi'),
                    macd=signal_data.get('macd'),
                    volume_ratio=signal_data.get('volume_ratio')
                )
                
                if 'metadata' in signal_data:
                    signal.set_metadata(signal_data['metadata'])
                
                session.add(signal)
                await session.commit()
                await session.refresh(signal)
                
                return signal.id
                
        except Exception as e:
            self.logger.error(f"Error saving signal: {str(e)}")
            return None
    
    async def update_signal_execution(self, signal_id: int, 
                                    execution_data: Dict) -> bool:
        """
        Sinyal execution bilgilerini güncelleme
        
        Args:
            signal_id: Signal ID
            execution_data: Execution bilgileri
            
        Returns:
            Güncelleme başarılı mı
        """
        try:
            async with self.async_session() as session:
                await session.execute(
                    update(Signal)
                    .where(Signal.id == signal_id)
                    .values(
                        executed=True,
                        execution_price=execution_data.get('execution_price'),
                        profit_loss=execution_data.get('profit_loss'),
                        executed_at=datetime.utcnow()
                    )
                )
                await session.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating signal execution: {str(e)}")
            return False
    
    # Alert operations
    async def create_alert(self, alert_type: str, message: str,
                         symbol: str = None, severity: str = 'info',
                         alert_data: Dict = None) -> Optional[int]:
        """
        Uyarı oluşturma
        
        Args:
            alert_type: Uyarı türü
            message: Uyarı mesajı
            symbol: İlgili sembol
            severity: Önem derecesi
            alert_data: Ek veri
            
        Returns:
            Alert ID
        """
        try:
            async with self.async_session() as session:
                alert = Alert(
                    alert_type=alert_type,
                    symbol=symbol,
                    message=message,
                    severity=severity
                )
                
                if alert_data:
                    alert.set_data(alert_data)
                
                session.add(alert)
                await session.commit()
                await session.refresh(alert)
                
                return alert.id
                
        except Exception as e:
            self.logger.error(f"Error creating alert: {str(e)}")
            return None
    
    async def get_unread_alerts(self, limit: int = 50) -> List[Dict]:
        """
        Okunmamış uyarılar
        
        Args:
            limit: Sonuç limiti
            
        Returns:
            Uyarı listesi
        """
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(Alert)
                    .where(Alert.is_read == False)
                    .where(Alert.is_dismissed == False)
                    .order_by(Alert.created_at.desc())
                    .limit(limit)
                )
                alerts = result.scalars().all()
                
                return [alert.to_dict() for alert in alerts]
                
        except Exception as e:
            self.logger.error(f"Error getting unread alerts: {str(e)}")
            return []
    
    async def mark_alert_read(self, alert_id: int) -> bool:
        """Uyarıyı okundu olarak işaretleme"""
        try:
            async with self.async_session() as session:
                await session.execute(
                    update(Alert)
                    .where(Alert.id == alert_id)
                    .values(is_read=True, read_at=datetime.utcnow())
                )
                await session.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error marking alert as read: {str(e)}")
            return False
    
    # Configuration operations
    async def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Konfigürasyon değeri alma
        
        Args:
            key: Konfigürasyon anahtarı
            default: Varsayılan değer
            
        Returns:
            Konfigürasyon değeri
        """
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(Configuration).where(Configuration.key == key)
                )
                config = result.scalar_one_or_none()
                
                if config:
                    return config.get_typed_value()
                else:
                    return default
                    
        except Exception as e:
            self.logger.error(f"Error getting config value: {str(e)}")
            return default
    
    async def set_config_value(self, key: str, value: Any, 
                             value_type: str = 'string',
                             description: str = None) -> bool:
        """
        Konfigürasyon değeri ayarlama
        
        Args:
            key: Konfigürasyon anahtarı
            value: Değer
            value_type: Değer türü
            description: Açıklama
            
        Returns:
            Ayarlama başarılı mı
        """
        try:
            async with self.async_session() as session:
                # Existing config kontrolü
                result = await session.execute(
                    select(Configuration).where(Configuration.key == key)
                )
                config = result.scalar_one_or_none()
                
                if config:
                    # Update existing
                    config.value = str(value)
                    config.value_type = value_type
                    config.updated_at = datetime.utcnow()
                    if description:
                        config.description = description
                else:
                    # Create new
                    config = Configuration(
                        key=key,
                        value=str(value),
                        value_type=value_type,
                        description=description
                    )
                    session.add(config)
                
                await session.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error setting config value: {str(e)}")
            return False
    
    # Performance analytics
    async def get_trading_statistics(self, days: int = 30) -> Dict:
        """
        Trading istatistikleri
        
        Args:
            days: Analiz periyodu
            
        Returns:
            Trading istatistikleri
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            async with self.async_session() as session:
                # Total trades
                total_trades_result = await session.execute(
                    select(func.count(Trade.id))
                    .where(Trade.created_at >= start_date)
                )
                total_trades = total_trades_result.scalar()
                
                # Winning trades
                winning_trades_result = await session.execute(
                    select(func.count(Trade.id))
                    .where(Trade.created_at >= start_date)
                    .where(Trade.profit_loss > 0)
                )
                winning_trades = winning_trades_result.scalar()
                
                # Total P&L
                total_pnl_result = await session.execute(
                    select(func.sum(Trade.profit_loss))
                    .where(Trade.created_at >= start_date)
                )
                total_pnl = total_pnl_result.scalar() or 0.0
                
                # Best and worst trades
                best_trade_result = await session.execute(
                    select(Trade)
                    .where(Trade.created_at >= start_date)
                    .order_by(Trade.profit_loss.desc())
                    .limit(1)
                )
                best_trade = best_trade_result.scalar_one_or_none()
                
                worst_trade_result = await session.execute(
                    select(Trade)
                    .where(Trade.created_at >= start_date)
                    .order_by(Trade.profit_loss.asc())
                    .limit(1)
                )
                worst_trade = worst_trade_result.scalar_one_or_none()
                
                # Win rate
                win_rate = winning_trades / total_trades if total_trades > 0 else 0
                
                return {
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': total_trades - winning_trades,
                    'win_rate': win_rate,
                    'total_pnl': total_pnl,
                    'average_pnl_per_trade': total_pnl / total_trades if total_trades > 0 else 0,
                    'best_trade': best_trade.to_dict() if best_trade else None,
                    'worst_trade': worst_trade.to_dict() if worst_trade else None,
                    'period_days': days
                }
                
        except Exception as e:
            self.logger.error(f"Error getting trading statistics: {str(e)}")
            return {}
    
    async def get_symbol_performance(self, symbol: str) -> Dict:
        """
        Sembol bazında performans
        
        Args:
            symbol: Sembol adı
            
        Returns:
            Sembol performansı
        """
        try:
            async with self.async_session() as session:
                # Symbol trades
                trades_result = await session.execute(
                    select(Trade).where(Trade.symbol == symbol)
                    .order_by(Trade.created_at.desc())
                )
                trades = trades_result.scalars().all()
                
                # Portfolio position
                portfolio_result = await session.execute(
                    select(Portfolio).where(Portfolio.symbol == symbol)
                )
                portfolio_position = portfolio_result.scalar_one_or_none()
                
                # Calculate metrics
                total_trades = len(trades)
                winning_trades = sum(1 for trade in trades if trade.profit_loss > 0)
                total_pnl = sum(trade.profit_loss for trade in trades)
                
                return {
                    'symbol': symbol,
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'win_rate': winning_trades / total_trades if total_trades > 0 else 0,
                    'total_realized_pnl': total_pnl,
                    'current_position': portfolio_position.to_dict() if portfolio_position else None,
                    'recent_trades': [trade.to_dict() for trade in trades[:10]]
                }
                
        except Exception as e:
            self.logger.error(f"Error getting symbol performance: {str(e)}")
            return {}
    
    # Cleanup operations
    async def cleanup_old_data(self, days_to_keep: int = 90) -> Dict:
        """
        Eski verileri temizleme
        
        Args:
            days_to_keep: Saklanacak gün sayısı
            
        Returns:
            Temizleme sonuçları
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleanup_results = {}
        
        try:
            async with self.async_session() as session:
                # Old market data
                market_data_result = await session.execute(
                    delete(MarketData).where(MarketData.created_at < cutoff_date)
                )
                cleanup_results['market_data_deleted'] = market_data_result.rowcount
                
                # Old signals
                signals_result = await session.execute(
                    delete(Signal).where(Signal.generated_at < cutoff_date)
                )
                cleanup_results['signals_deleted'] = signals_result.rowcount
                
                # Old alerts (read and dismissed)
                alerts_result = await session.execute(
                    delete(Alert)
                    .where(Alert.created_at < cutoff_date)
                    .where(Alert.is_read == True)
                    .where(Alert.is_dismissed == True)
                )
                cleanup_results['alerts_deleted'] = alerts_result.rowcount
                
                await session.commit()
                
                self.logger.info(f"Cleanup completed: {cleanup_results}")
                
        except Exception as e:
            self.logger.error(f"Error in cleanup: {str(e)}")
            cleanup_results['error'] = str(e)
            
        return cleanup_results
    
    async def get_database_stats(self) -> Dict:
        """
        Database istatistikleri
        
        Returns:
            Database stats
        """
        try:
            async with self.async_session() as session:
                stats = {}
                
                # Table row counts
                tables = [Trade, Portfolio, PerformanceMetrics, Signal, 
                         MarketData, Alert, Configuration, SentimentRecord]
                
                for table in tables:
                    result = await session.execute(select(func.count(table.id)))
                    count = result.scalar()
                    stats[f"{table.__tablename__}_count"] = count
                
                # Latest updates
                latest_trade_result = await session.execute(
                    select(Trade.created_at).order_by(Trade.created_at.desc()).limit(1)
                )
                latest_trade = latest_trade_result.scalar()
                stats['latest_trade'] = latest_trade.isoformat() if latest_trade else None
                
                latest_performance_result = await session.execute(
                    select(PerformanceMetrics.date).order_by(PerformanceMetrics.date.desc()).limit(1)
                )
                latest_performance = latest_performance_result.scalar()
                stats['latest_performance'] = latest_performance.isoformat() if latest_performance else None
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting database stats: {str(e)}")
            return {}