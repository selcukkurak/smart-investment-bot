"""
Smart Investment Bot - Main Bot Class
Orchestrates the entire trading system
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import schedule
import time

from .profit_calculator import ProfitCalculator
from .risk_manager import RiskManager
from .portfolio_manager import PortfolioManager, AssetType
from ..apis.yahoo_finance_client import YahooFinanceClient
from ..apis.binance_client import BinanceClient
from ..strategies.scalping_strategy import ScalpingStrategy
from ..utils.config import Config
from ..utils.logger import bot_logger


class SmartInvestmentBot:
    """
    Main Smart Investment Bot that orchestrates trading across multiple assets
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        # Load configuration
        self.config = Config(config_path)
        
        # Validate configuration
        config_issues = self.config.validate_config()
        if config_issues:
            bot_logger.error(f"Configuration issues: {config_issues}")
        
        # Initialize core components
        trading_config = self.config.get_trading_config()
        risk_config = self.config.get_risk_config()
        
        initial_capital = trading_config.get('initial_capital', 10000)
        
        self.profit_calculator = ProfitCalculator(initial_capital)
        self.risk_manager = RiskManager(
            max_daily_loss_rate=risk_config.get('max_daily_loss', 0.02),
            max_position_rate=trading_config.get('position_size_percent', 0.1),
            max_drawdown_rate=risk_config.get('drawdown_limit', 0.05)
        )
        self.portfolio = PortfolioManager(initial_capital)
        
        # Initialize API clients
        self.yahoo_client = YahooFinanceClient()
        
        binance_config = self.config.get_api_config('binance')
        if binance_config.get('api_key'):
            self.binance_client = BinanceClient(
                api_key=binance_config.get('api_key', ''),
                secret_key=binance_config.get('secret_key', ''),
                sandbox=binance_config.get('sandbox', True)
            )
        else:
            self.binance_client = None
            bot_logger.warning("Binance API credentials not configured")
        
        # Initialize strategies
        self.strategies = {
            'scalping': ScalpingStrategy()
        }
        
        # Bot state
        self.is_running = False
        self.trading_enabled = True
        self.start_time = None
        self.daily_opening_balance = initial_capital
        
        bot_logger.log_system_event("Bot initialized", f"Capital: ${initial_capital}")
    
    async def start(self) -> None:
        """Start the trading bot"""
        bot_logger.log_system_event("Starting Smart Investment Bot")
        
        self.is_running = True
        self.start_time = datetime.now()
        self.daily_opening_balance = self.portfolio.get_portfolio_value()
        
        # Test API connections
        await self._test_api_connections()
        
        # Schedule daily tasks
        schedule.every().day.at("09:00").do(self._daily_reset)
        schedule.every().day.at("17:00").do(self._daily_summary)
        schedule.every(5).minutes.do(self._scan_markets)
        schedule.every(1).minutes.do(self._check_positions)
        
        bot_logger.info("Bot started successfully")
        
        # Main trading loop
        await self._main_loop()
    
    async def stop(self) -> None:
        """Stop the trading bot"""
        bot_logger.log_system_event("Stopping Smart Investment Bot")
        self.is_running = False
        
        # Close all open positions
        await self._close_all_positions()
        
        # Generate final report
        performance = self.profit_calculator.get_performance_report()
        bot_logger.log_performance(
            performance.get('total_return_rate', 0) * 100,
            1.0,  # 1% target
            performance.get('total_return_rate', 0) * 100,
            performance.get('current_capital', 0)
        )
        
        bot_logger.log_system_event("Bot stopped")
    
    async def _test_api_connections(self) -> None:
        """Test all API connections"""
        bot_logger.info("Testing API connections...")
        
        # Test Yahoo Finance (always available)
        test_price = self.yahoo_client.get_current_price('AAPL')
        if test_price:
            bot_logger.info(f"Yahoo Finance connected successfully (AAPL: ${test_price})")
        else:
            bot_logger.error("Yahoo Finance connection failed")
        
        # Test Binance if configured
        if self.binance_client:
            connected = await self.binance_client.connect()
            if connected:
                bot_logger.info("Binance connected successfully")
            else:
                bot_logger.error("Binance connection failed")
    
    async def _main_loop(self) -> None:
        """Main trading loop"""
        while self.is_running:
            try:
                # Run scheduled tasks
                schedule.run_pending()
                
                # Check for trading opportunities
                if self.trading_enabled:
                    await self._execute_trading_cycle()
                
                # Sleep for 1 minute
                await asyncio.sleep(60)
                
            except Exception as e:
                bot_logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(10)  # Short sleep on error
    
    async def _execute_trading_cycle(self) -> None:
        """Execute one trading cycle"""
        current_balance = self.portfolio.get_portfolio_value()
        
        # Check if we can trade (risk limits)
        can_trade, reason = self.risk_manager.should_allow_trade(
            current_balance, self.daily_opening_balance, 0
        )
        
        if not can_trade:
            bot_logger.log_risk_event("Trading disabled", reason)
            return
        
        # Get market opportunities
        opportunities = await self._find_trading_opportunities()
        
        # Execute trades based on opportunities
        for opportunity in opportunities:
            await self._execute_trade(opportunity)
    
    async def _find_trading_opportunities(self) -> List[Dict]:
        """Scan markets for trading opportunities"""
        opportunities = []
        
        # Get supported assets from config
        assets_config = self.config.get('assets', {})
        
        # Scan crypto markets
        if self.binance_client:
            crypto_symbols = assets_config.get('cryptocurrencies', ['BTC/USDT'])
            for symbol in crypto_symbols[:3]:  # Limit to 3 for demo
                opportunity = await self._analyze_crypto_opportunity(symbol)
                if opportunity:
                    opportunities.append(opportunity)
        
        # Scan stock markets
        stock_symbols = assets_config.get('stocks', ['AAPL'])
        for symbol in stock_symbols[:3]:  # Limit to 3 for demo
            opportunity = await self._analyze_stock_opportunity(symbol)
            if opportunity:
                opportunities.append(opportunity)
        
        return opportunities
    
    async def _analyze_crypto_opportunity(self, symbol: str) -> Optional[Dict]:
        """Analyze cryptocurrency for trading opportunity"""
        try:
            if not self.binance_client:
                return None
            
            # Get market data
            klines = self.binance_client.get_klines(symbol, '5m', 100)
            if klines is None or len(klines) < 50:
                return None
            
            # Add indicators and analyze with scalping strategy
            klines = self.strategies['scalping'].add_technical_indicators(klines)
            signal = self.strategies['scalping'].analyze(symbol, klines)
            
            if signal.signal_type.value != 'hold' and signal.confidence >= 0.65:
                return {
                    'symbol': symbol,
                    'asset_type': 'crypto',
                    'signal': signal,
                    'current_price': signal.price,
                    'api_client': 'binance'
                }
        
        except Exception as e:
            bot_logger.log_api_error("Binance", f"analyze {symbol}", str(e))
        
        return None
    
    async def _analyze_stock_opportunity(self, symbol: str) -> Optional[Dict]:
        """Analyze stock for trading opportunity"""
        try:
            # Get market data from Yahoo Finance
            historical_data = self.yahoo_client.get_historical_data(symbol, '1d', '5m')
            if historical_data is None or len(historical_data) < 50:
                return None
            
            # Prepare data for analysis
            df = historical_data.reset_index()
            df.columns = df.columns.str.lower()
            
            # Add indicators and analyze
            df = self.strategies['scalping'].add_technical_indicators(df)
            signal = self.strategies['scalping'].analyze(symbol, df)
            
            if signal.signal_type.value != 'hold' and signal.confidence >= 0.65:
                return {
                    'symbol': symbol,
                    'asset_type': 'stock',
                    'signal': signal,
                    'current_price': signal.price,
                    'api_client': 'yahoo'
                }
        
        except Exception as e:
            bot_logger.log_api_error("Yahoo Finance", f"analyze {symbol}", str(e))
        
        return None
    
    async def _execute_trade(self, opportunity: Dict) -> None:
        """Execute a trade based on opportunity"""
        signal = opportunity['signal']
        symbol = opportunity['symbol']
        current_price = opportunity['current_price']
        
        # Calculate position size
        current_balance = self.portfolio.get_portfolio_value()
        base_position_size = self.risk_manager.calculate_position_size(current_balance)
        
        # Adjust for risk
        risk_level = self.risk_manager.assess_market_risk(0.02, 1.0, 0.01)  # Sample values
        position_size = self.risk_manager.get_risk_adjusted_position_size(
            base_position_size, risk_level
        )
        
        quantity = position_size / current_price
        
        # Check if trade is allowed
        can_trade, reason = self.risk_manager.should_allow_trade(
            current_balance, self.daily_opening_balance, position_size
        )
        
        if not can_trade:
            bot_logger.log_risk_event("Trade blocked", f"{symbol}: {reason}")
            return
        
        # Execute trade (demo mode for now)
        if signal.signal_type.value == 'buy':
            success = await self._execute_buy_order(symbol, quantity, current_price, opportunity)
        elif signal.signal_type.value == 'sell':
            success = await self._execute_sell_order(symbol, quantity, current_price, opportunity)
        else:
            return
        
        if success:
            bot_logger.log_signal(
                'scalping', symbol, signal.signal_type.value, 
                signal.confidence, signal.reasoning
            )
    
    async def _execute_buy_order(self, symbol: str, quantity: float, 
                               price: float, opportunity: Dict) -> bool:
        """Execute buy order"""
        try:
            # For demo, use portfolio manager directly
            commission = quantity * price * 0.001  # 0.1% commission
            success = self.portfolio.buy_asset(symbol, quantity, price, commission)
            
            if success:
                # Add position tracking
                stop_loss = self.risk_manager.calculate_stop_loss_price(price, 'long', 0.0025)
                take_profit = self.risk_manager.calculate_take_profit_price(price, 'long', 0.005)
                
                position_id = self.risk_manager.add_position(
                    symbol, 'long', price, quantity, stop_loss, take_profit
                )
                
                bot_logger.log_trade('BUY', symbol, quantity, price, True, 
                                   f"Position ID: {position_id}")
                return True
            else:
                bot_logger.log_trade('BUY', symbol, quantity, price, False, "Insufficient funds")
                
        except Exception as e:
            bot_logger.log_trade('BUY', symbol, quantity, price, False, str(e))
        
        return False
    
    async def _execute_sell_order(self, symbol: str, quantity: float, 
                                price: float, opportunity: Dict) -> bool:
        """Execute sell order"""
        try:
            # Check if we have the asset to sell
            if symbol not in self.portfolio.assets:
                return False
            
            available_quantity = self.portfolio.assets[symbol].quantity
            sell_quantity = min(quantity, available_quantity)
            
            if sell_quantity <= 0:
                return False
            
            commission = sell_quantity * price * 0.001
            success = self.portfolio.sell_asset(symbol, sell_quantity, price, commission)
            
            if success:
                bot_logger.log_trade('SELL', symbol, sell_quantity, price, True)
                return True
            else:
                bot_logger.log_trade('SELL', symbol, sell_quantity, price, False, "Sale failed")
                
        except Exception as e:
            bot_logger.log_trade('SELL', symbol, quantity, price, False, str(e))
        
        return False
    
    def _daily_reset(self) -> None:
        """Reset daily counters and balances"""
        bot_logger.log_system_event("Daily reset")
        
        # Record yesterday's performance
        current_balance = self.portfolio.get_portfolio_value()
        yesterday_trades = [
            t for t in self.portfolio.transaction_history
            if t['timestamp'].date() == (datetime.now() - timedelta(days=1)).date()
        ]
        
        daily_performance = self.profit_calculator.track_daily_performance(
            datetime.now() - timedelta(days=1),
            self.daily_opening_balance,
            current_balance,
            yesterday_trades
        )
        
        # Set new daily opening balance
        self.daily_opening_balance = current_balance
        
        # Take portfolio snapshot
        self.portfolio.take_daily_snapshot()
        
        bot_logger.log_performance(
            daily_performance['daily_return_rate'] * 100,
            daily_performance['target_rate'] * 100,
            self.profit_calculator.get_performance_report()['total_return_rate'] * 100,
            current_balance
        )
    
    def _daily_summary(self) -> None:
        """Generate daily summary report"""
        bot_logger.log_system_event("Generating daily summary")
        
        performance = self.profit_calculator.get_performance_report()
        portfolio_summary = self.portfolio.get_performance_summary()
        risk_metrics = self.risk_manager.get_risk_metrics(self.portfolio.get_portfolio_value())
        
        bot_logger.info(f"Daily Summary:")
        bot_logger.info(f"  Portfolio Value: ${portfolio_summary['current_portfolio_value']:.2f}")
        bot_logger.info(f"  Total Return: {portfolio_summary['total_return_percent']:.2f}%")
        bot_logger.info(f"  Active Positions: {risk_metrics['active_positions']}")
        bot_logger.info(f"  Target Success Rate: {performance.get('target_success_rate', 0):.1%}")
    
    def _scan_markets(self) -> None:
        """Scheduled market scanning"""
        try:
            # This will be called by the main loop, just log for now
            bot_logger.debug("Market scan scheduled")
        except Exception as e:
            bot_logger.error(f"Market scan error: {e}")
    
    def _check_positions(self) -> None:
        """Check open positions for stop loss/take profit"""
        try:
            for position in self.risk_manager.current_positions:
                symbol = position['symbol']
                
                # Get current price
                current_price = self.yahoo_client.get_current_price(symbol)
                if not current_price:
                    continue
                
                # Check stop loss and take profit
                should_close = False
                reason = ""
                
                if position['type'].lower() == 'long':
                    if current_price <= position['stop_loss']:
                        should_close = True
                        reason = "Stop loss triggered"
                    elif current_price >= position['take_profit']:
                        should_close = True
                        reason = "Take profit triggered"
                else:  # short position
                    if current_price >= position['stop_loss']:
                        should_close = True
                        reason = "Stop loss triggered"
                    elif current_price <= position['take_profit']:
                        should_close = True
                        reason = "Take profit triggered"
                
                if should_close:
                    # Close position
                    closed_position = self.risk_manager.close_position(
                        position['id'], current_price, reason
                    )
                    
                    if closed_position:
                        # Update portfolio
                        self.portfolio.sell_asset(
                            symbol, position['quantity'], current_price
                        )
                        
                        bot_logger.log_trade(
                            'CLOSE', symbol, position['quantity'], 
                            current_price, True, reason
                        )
        
        except Exception as e:
            bot_logger.error(f"Position check error: {e}")
    
    async def _close_all_positions(self) -> None:
        """Close all open positions"""
        for position in self.risk_manager.current_positions.copy():
            symbol = position['symbol']
            current_price = self.yahoo_client.get_current_price(symbol)
            
            if current_price:
                closed_position = self.risk_manager.close_position(
                    position['id'], current_price, "Bot shutdown"
                )
                
                if closed_position:
                    self.portfolio.sell_asset(
                        symbol, position['quantity'], current_price
                    )
                    
                    bot_logger.log_trade(
                        'CLOSE', symbol, position['quantity'], 
                        current_price, True, "Bot shutdown"
                    )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status"""
        return {
            'is_running': self.is_running,
            'trading_enabled': self.trading_enabled,
            'start_time': self.start_time,
            'uptime_minutes': (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else 0,
            'portfolio_value': self.portfolio.get_portfolio_value(),
            'daily_target': self.profit_calculator.get_dynamic_target_for_date(datetime.now()),
            'active_positions': len(self.risk_manager.current_positions),
            'cash_balance': self.portfolio.cash_balance,
            'total_return': self.portfolio.get_portfolio_value() - self.profit_calculator.initial_capital
        }
    
    def enable_trading(self) -> None:
        """Enable trading"""
        self.trading_enabled = True
        bot_logger.log_system_event("Trading enabled")
    
    def disable_trading(self) -> None:
        """Disable trading"""
        self.trading_enabled = False
        bot_logger.log_system_event("Trading disabled")
    
    async def manual_trade(self, symbol: str, action: str, quantity: float) -> bool:
        """Execute manual trade"""
        current_price = self.yahoo_client.get_current_price(symbol)
        if not current_price:
            bot_logger.error(f"Could not get price for {symbol}")
            return False
        
        if action.lower() == 'buy':
            return await self._execute_buy_order(symbol, quantity, current_price, {})
        elif action.lower() == 'sell':
            return await self._execute_sell_order(symbol, quantity, current_price, {})
        
        return False