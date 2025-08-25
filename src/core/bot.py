"""
Smart Investment Bot - Ana bot sınıfı
Multi-asset trading bot with risk management and profit optimization
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import numpy as np

from .profit_calculator import ProfitCalculator
from .risk_manager import RiskManager, Position
from .portfolio_manager import PortfolioManager, AssetType


class TradingMode(Enum):
    """Trading modları"""
    LIVE = "live"
    PAPER = "paper"
    BACKTEST = "backtest"


class SmartInvestmentBot:
    """
    Smart Investment Bot ana sınıfı
    
    Özellikler:
    - Multi-asset trading (crypto, stocks, forex)
    - Profit optimization with compound growth
    - Risk management and position sizing
    - Real-time market monitoring
    - Automated trading strategies
    """
    
    def __init__(self, initial_capital: float = 10000.0, 
                 trading_mode: TradingMode = TradingMode.PAPER):
        """
        Bot başlatma
        
        Args:
            initial_capital: Başlangıç sermayesi
            trading_mode: Trading modu
        """
        self.initial_capital = initial_capital
        self.trading_mode = trading_mode
        self.is_running = False
        self.is_trading_enabled = True
        
        # Core components
        self.profit_calculator = ProfitCalculator(initial_capital)
        self.risk_manager = RiskManager()
        self.portfolio_manager = PortfolioManager(initial_capital)
        
        # API clients (will be initialized later)
        self.api_clients = {}
        self.strategies = {}
        self.analysis_tools = {}
        
        # Bot state
        self.last_update = None
        self.error_count = 0
        self.max_errors = 10
        
        # Performance tracking
        self.daily_stats = {}
        self.alerts = []
        
        # Logger
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Logger kurulumu"""
        logger = logging.getLogger('SmartInvestmentBot')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    async def initialize(self) -> bool:
        """
        Bot bileşenlerini başlatma
        
        Returns:
            Başlatma başarılı mı
        """
        try:
            self.logger.info("🚀 Initializing Smart Investment Bot...")
            
            # API clients initialization (placeholder)
            await self._initialize_api_clients()
            
            # Strategies initialization
            await self._initialize_strategies()
            
            # Analysis tools initialization
            await self._initialize_analysis_tools()
            
            # Initial portfolio setup
            await self._setup_initial_portfolio()
            
            self.logger.info("✅ Bot initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Bot initialization failed: {str(e)}")
            return False
    
    async def _initialize_api_clients(self) -> None:
        """API client'ları başlatma"""
        # Placeholder for API clients
        self.api_clients = {
            'binance': None,  # Will be BinanceClient instance
            'yahoo_finance': None,  # Will be YahooFinanceClient instance
            'alpha_vantage': None  # Will be AlphaVantageClient instance
        }
        self.logger.info("📡 API clients initialized")
    
    async def _initialize_strategies(self) -> None:
        """Trading stratejilerini başlatma"""
        # Placeholder for strategies
        self.strategies = {
            'scalping': None,  # Will be ScalpingStrategy instance
            'swing': None  # Will be SwingStrategy instance
        }
        self.logger.info("📈 Trading strategies initialized")
    
    async def _initialize_analysis_tools(self) -> None:
        """Analiz araçlarını başlatma"""
        # Placeholder for analysis tools
        self.analysis_tools = {
            'technical': None,  # Will be TechnicalAnalysis instance
            'scanner': None,  # Will be MarketScanner instance
            'sentiment': None  # Will be SentimentAnalysis instance
        }
        self.logger.info("🔍 Analysis tools initialized")
    
    async def _setup_initial_portfolio(self) -> None:
        """İlk portföy kurulumu"""
        # Desteklenen varlıkları ekle
        supported_assets = [
            ('BTC/USDT', AssetType.CRYPTO, 50000.0),
            ('ETH/USDT', AssetType.CRYPTO, 3000.0),
            ('AAPL', AssetType.STOCK, 150.0),
            ('MSFT', AssetType.STOCK, 300.0),
            ('EUR/USD', AssetType.FOREX, 1.1),
            ('GBP/USD', AssetType.FOREX, 1.25)
        ]
        
        for symbol, asset_type, price in supported_assets:
            self.portfolio_manager.add_asset(symbol, asset_type, price)
            
        self.logger.info(f"📊 Initial portfolio setup with {len(supported_assets)} assets")
    
    async def start(self) -> None:
        """
        Bot'u başlatma ve ana loop
        """
        if self.is_running:
            self.logger.warning("⚠️ Bot is already running")
            return
            
        self.is_running = True
        self.logger.info("🟢 Smart Investment Bot started")
        
        try:
            while self.is_running:
                await self._main_loop()
                await asyncio.sleep(60)  # 1 dakika bekleme
                
        except KeyboardInterrupt:
            self.logger.info("🔴 Bot stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Bot crashed: {str(e)}")
            self.error_count += 1
            
            if self.error_count >= self.max_errors:
                self.logger.error("🚨 Maximum error count reached, stopping bot")
                await self.stop()
        finally:
            self.is_running = False
    
    async def _main_loop(self) -> None:
        """Ana bot loop"""
        try:
            # 1. Market data güncelleme
            await self._update_market_data()
            
            # 2. Portfolio güncelleme
            await self._update_portfolio()
            
            # 3. Risk kontrolü
            await self._check_risks()
            
            # 4. Trading sinyalleri kontrol
            if self.is_trading_enabled:
                await self._check_trading_signals()
            
            # 5. Performance tracking
            await self._update_performance_stats()
            
            # 6. Günlük hedef kontrolü
            await self._check_daily_targets()
            
            self.last_update = datetime.now()
            self.error_count = 0  # Reset error count on successful loop
            
        except Exception as e:
            self.logger.error(f"❌ Error in main loop: {str(e)}")
            self.error_count += 1
    
    async def _update_market_data(self) -> None:
        """Market verilerini güncelleme"""
        # Placeholder - gerçek implementasyonda API client'lardan veri çekilecek
        price_updates = {}
        
        # Simulated price updates
        for symbol in self.portfolio_manager.assets:
            # Basit random price movement simulation
            current_asset = self.portfolio_manager.assets[symbol]
            change_pct = np.random.uniform(-0.02, 0.02)  # ±%2 değişim
            new_price = current_asset.current_price * (1 + change_pct)
            price_updates[symbol] = new_price
            
        # Portfolio manager'da fiyatları güncelle
        updated_count = self.portfolio_manager.update_prices(price_updates)
        
        # Risk manager'da pozisyon fiyatlarını güncelle
        for symbol, new_price in price_updates.items():
            self.risk_manager.update_position_price(symbol, new_price)
            
        self.logger.debug(f"📊 Updated {updated_count} asset prices")
    
    async def _update_portfolio(self) -> None:
        """Portföy durumunu güncelleme"""
        # Portfolio summary
        summary = self.portfolio_manager.get_portfolio_summary()
        
        # Risk assessment
        risk_summary = self.risk_manager.get_risk_summary(
            self.portfolio_manager.get_portfolio_value()
        )
        
        # Performance metrics
        performance = self.portfolio_manager.get_performance_metrics()
        
        self.logger.debug(
            f"💼 Portfolio Value: ${performance['total_value']:.2f} "
            f"({performance['total_return_percentage']:.2%})"
        )
    
    async def _check_risks(self) -> None:
        """Risk kontrollerini yapma"""
        capital = self.portfolio_manager.get_portfolio_value()
        
        # Stop-loss kontrolü
        stop_loss_triggers = self.risk_manager.check_stop_loss_triggers()
        for symbol in stop_loss_triggers:
            await self._execute_stop_loss(symbol)
            
        # Take-profit kontrolü
        take_profit_triggers = self.risk_manager.check_take_profit_triggers()
        for symbol in take_profit_triggers:
            await self._execute_take_profit(symbol)
            
        # Portfolio risk kontrolü
        risk_assessment = self.risk_manager.assess_portfolio_risk(capital)
        if risk_assessment['risk_level'].value in ['high', 'extreme']:
            self.alerts.append({
                'timestamp': datetime.now(),
                'type': 'RISK_WARNING',
                'message': f"High portfolio risk detected: {risk_assessment['risk_level'].value}",
                'details': risk_assessment
            })
    
    async def _execute_stop_loss(self, symbol: str) -> None:
        """Stop-loss emri çalıştırma"""
        if symbol in self.portfolio_manager.assets:
            asset = self.portfolio_manager.assets[symbol]
            if asset.amount > 0:
                # Stop-loss satışı (simulated)
                result = self.portfolio_manager.sell_asset(
                    symbol, asset.amount, asset.current_price
                )
                
                if result['success']:
                    self.logger.warning(
                        f"🛑 Stop-loss triggered for {symbol}: "
                        f"PnL: ${result['realized_pnl']:.2f}"
                    )
                    
                    # Risk manager'dan pozisyonu kaldır
                    self.risk_manager.remove_position(symbol)
    
    async def _execute_take_profit(self, symbol: str) -> None:
        """Take-profit emri çalıştırma"""
        if symbol in self.portfolio_manager.assets:
            asset = self.portfolio_manager.assets[symbol]
            if asset.amount > 0:
                # Take-profit satışı (partial - %50)
                sell_amount = asset.amount * 0.5
                result = self.portfolio_manager.sell_asset(
                    symbol, sell_amount, asset.current_price
                )
                
                if result['success']:
                    self.logger.info(
                        f"🎯 Take-profit triggered for {symbol}: "
                        f"PnL: ${result['realized_pnl']:.2f}"
                    )
    
    async def _check_trading_signals(self) -> None:
        """Trading sinyallerini kontrol etme"""
        # Placeholder for trading signal logic
        # Gerçek implementasyonda strategy pattern kullanılacak
        pass
    
    async def _update_performance_stats(self) -> None:
        """Performans istatistiklerini güncelleme"""
        today = datetime.now().date()
        
        # Günlük performans
        daily_performance = self.profit_calculator.get_daily_performance(today)
        self.daily_stats[today.isoformat()] = daily_performance
        
        # Hedef kontrol
        if not daily_performance['target_achieved']:
            remaining_target = self.profit_calculator.daily_target_profit - daily_performance['profit_rate']
            self.logger.info(
                f"📊 Daily target progress: {daily_performance['profit_rate']:.2%} "
                f"(Remaining: {remaining_target:.2%})"
            )
    
    async def _check_daily_targets(self) -> None:
        """Günlük hedefleri kontrol etme"""
        now = datetime.now()
        current_day = now.day
        
        # Gerekli günlük kazanç hesaplama
        required_profit = self.profit_calculator.calculate_required_daily_profit(
            current_day, now.month
        )
        
        current_performance = self.profit_calculator.get_daily_performance()
        
        if current_performance['profit_rate'] < self.profit_calculator.daily_target_profit:
            self.logger.warning(
                f"⏰ Daily target not met: {current_performance['profit_rate']:.2%} "
                f"(Target: {self.profit_calculator.daily_target_profit:.2%})"
            )
    
    async def stop(self) -> None:
        """Bot'u durdurma"""
        self.is_running = False
        self.logger.info("🔴 Smart Investment Bot stopped")
    
    def enable_trading(self) -> None:
        """Trading'i aktifleştirme"""
        self.is_trading_enabled = True
        self.logger.info("✅ Trading enabled")
    
    def disable_trading(self) -> None:
        """Trading'i deaktifleştirme"""
        self.is_trading_enabled = False
        self.logger.warning("❌ Trading disabled")
    
    def get_bot_status(self) -> Dict:
        """
        Bot durumu bilgileri
        
        Returns:
            Bot status dictionary
        """
        portfolio_value = self.portfolio_manager.get_portfolio_value()
        performance = self.portfolio_manager.get_performance_metrics()
        risk_summary = self.risk_manager.get_risk_summary(portfolio_value)
        
        return {
            'is_running': self.is_running,
            'is_trading_enabled': self.is_trading_enabled,
            'trading_mode': self.trading_mode.value,
            'last_update': self.last_update,
            'error_count': self.error_count,
            'uptime': datetime.now() - (self.last_update or datetime.now()),
            'portfolio': {
                'total_value': portfolio_value,
                'total_return': performance['total_return'],
                'total_return_percentage': performance['total_return_percentage'],
                'cash_balance': self.portfolio_manager.cash_balance,
                'active_positions': len([a for a in self.portfolio_manager.assets.values() if a.amount > 0])
            },
            'risk': {
                'level': risk_summary['risk_level'].value,
                'score': risk_summary['risk_score'],
                'var_95': risk_summary['var_95']
            },
            'recent_alerts': self.alerts[-5:] if self.alerts else []
        }
    
    async def execute_trade(self, symbol: str, action: str, amount: float,
                          price: float = None, strategy: str = None) -> Dict:
        """
        Manuel trade çalıştırma
        
        Args:
            symbol: Sembol adı
            action: 'BUY' veya 'SELL'
            amount: İşlem miktarı
            price: Fiyat (opsiyonel, mevcut fiyat kullanılır)
            strategy: Kullanılan strateji
            
        Returns:
            İşlem sonucu
        """
        if not self.is_trading_enabled:
            return {
                'success': False,
                'message': 'Trading is disabled'
            }
        
        try:
            # Current price al
            if price is None:
                if symbol in self.portfolio_manager.assets:
                    price = self.portfolio_manager.assets[symbol].current_price
                else:
                    return {
                        'success': False,
                        'message': f'Asset {symbol} not found'
                    }
            
            # Risk validation
            capital = self.portfolio_manager.get_portfolio_value()
            validation = self.risk_manager.validate_new_trade(
                symbol, amount, price, capital
            )
            
            if not validation['approved']:
                return {
                    'success': False,
                    'message': 'Trade rejected by risk manager',
                    'errors': validation['errors']
                }
            
            # Execute trade
            if action.upper() == 'BUY':
                result = self.portfolio_manager.buy_asset(symbol, amount, price)
            elif action.upper() == 'SELL':
                result = self.portfolio_manager.sell_asset(symbol, amount, price)
            else:
                return {
                    'success': False,
                    'message': f'Invalid action: {action}'
                }
            
            if result['success']:
                # Risk manager'da pozisyon güncelleme
                if action.upper() == 'BUY':
                    stop_loss = self.risk_manager.calculate_stop_loss(price, 'long')
                    take_profit = self.risk_manager.calculate_take_profit(
                        price, stop_loss, 'long'
                    )
                    
                    self.risk_manager.add_position(
                        symbol, amount, price, price, stop_loss, take_profit
                    )
                
                # Profit calculator'da trade kaydı
                profit_loss = result.get('realized_pnl', 0)
                self.profit_calculator.record_trade(
                    action.upper(), symbol, amount, price,
                    exit_price=price if action.upper() == 'SELL' else None,
                    profit_loss=profit_loss
                )
                
                self.logger.info(
                    f"✅ {action.upper()} {amount} {symbol} at ${price:.2f} "
                    f"(Strategy: {strategy or 'manual'})"
                )
                
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Trade execution error: {str(e)}")
            return {
                'success': False,
                'message': f'Execution error: {str(e)}'
            }
    
    async def get_market_opportunities(self) -> List[Dict]:
        """
        Piyasa fırsatlarını tarama
        
        Returns:
            Fırsat listesi
        """
        opportunities = []
        
        # Placeholder for opportunity scanning
        # Gerçek implementasyonda technical analysis ve market scanner kullanılacak
        
        for symbol, asset in self.portfolio_manager.assets.items():
            # Basit momentum kontrolü
            if asset.amount == 0:  # Henüz pozisyon yok
                # Simulated opportunity
                opportunity_score = np.random.uniform(0, 1)
                if opportunity_score > 0.7:
                    opportunities.append({
                        'symbol': symbol,
                        'asset_type': asset.asset_type.value,
                        'action': 'BUY',
                        'confidence': opportunity_score,
                        'target_price': asset.current_price * 1.05,
                        'stop_loss': asset.current_price * 0.98,
                        'reason': 'Technical breakout pattern detected'
                    })
        
        # Confidence'a göre sırala
        opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        
        return opportunities[:5]  # En iyi 5 fırsat
    
    def get_daily_report(self) -> Dict:
        """
        Günlük rapor oluşturma
        
        Returns:
            Günlük rapor
        """
        today = datetime.now().date()
        
        # Performance metrics
        performance = self.portfolio_manager.get_performance_metrics()
        daily_performance = self.profit_calculator.get_daily_performance(today)
        
        # Portfolio summary
        portfolio_summary = self.portfolio_manager.get_portfolio_summary()
        
        # Risk analysis
        risk_summary = self.risk_manager.get_risk_summary(
            performance['total_value']
        )
        
        return {
            'date': today.isoformat(),
            'portfolio_value': performance['total_value'],
            'daily_return': daily_performance['profit_rate'],
            'total_return': performance['total_return_percentage'],
            'target_achieved': daily_performance['target_achieved'],
            'trades_today': daily_performance['trades_count'],
            'cash_balance': self.portfolio_manager.cash_balance,
            'risk_level': risk_summary['risk_level'].value,
            'active_positions': len([a for a in self.portfolio_manager.assets.values() if a.amount > 0]),
            'top_performers': self.portfolio_manager.get_top_performers(3),
            'alerts_count': len(self.alerts),
            'bot_status': 'Running' if self.is_running else 'Stopped'
        }
    
    async def emergency_stop(self) -> Dict:
        """
        Acil durum durdurma - tüm pozisyonları kapat
        
        Returns:
            Acil durum işlem sonuçları
        """
        self.logger.warning("🚨 EMERGENCY STOP INITIATED")
        
        results = []
        
        # Tüm pozisyonları sat
        for symbol, asset in self.portfolio_manager.assets.items():
            if asset.amount > 0:
                result = await self.execute_trade(
                    symbol, 'SELL', asset.amount, asset.current_price, 'emergency'
                )
                results.append({
                    'symbol': symbol,
                    'result': result
                })
        
        # Trading'i deaktifleştir
        self.disable_trading()
        
        return {
            'timestamp': datetime.now(),
            'closed_positions': len(results),
            'results': results,
            'final_cash_balance': self.portfolio_manager.cash_balance
        }