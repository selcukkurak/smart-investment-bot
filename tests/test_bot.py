"""
Test for Smart Investment Bot
Integration tests for bot functionality
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.bot import SmartInvestmentBot, TradingMode


class TestSmartInvestmentBot:
    """Bot integration test sınıfı"""
    
    def setup_method(self):
        """Her test öncesi çalışır"""
        self.bot = SmartInvestmentBot(initial_capital=10000.0, trading_mode=TradingMode.PAPER)
    
    @pytest.mark.asyncio
    async def test_bot_initialization(self):
        """Bot başlatma testi"""
        success = await self.bot.initialize()
        assert success is True
        assert self.bot.initial_capital == 10000.0
        assert self.bot.trading_mode == TradingMode.PAPER
        assert self.bot.profit_calculator is not None
        assert self.bot.risk_manager is not None
        assert self.bot.portfolio_manager is not None
    
    @pytest.mark.asyncio
    async def test_bot_status(self):
        """Bot durumu testi"""
        await self.bot.initialize()
        
        status = self.bot.get_bot_status()
        
        assert 'is_running' in status
        assert 'is_trading_enabled' in status
        assert 'trading_mode' in status
        assert 'portfolio' in status
        assert 'risk' in status
        
        assert status['trading_mode'] == 'paper'
        assert status['portfolio']['total_value'] == 10000.0
    
    @pytest.mark.asyncio
    async def test_manual_trade_execution(self):
        """Manuel trade çalıştırma testi"""
        await self.bot.initialize()
        
        # BUY trade
        result = await self.bot.execute_trade(
            symbol='BTC/USDT',
            action='BUY',
            amount=0.1,
            price=50000.0,
            strategy='test'
        )
        
        # Trade başarılı olmalı (paper trading mode)
        assert result['success'] is True
        
        # Portfolio'da pozisyon olmalı
        portfolio_summary = self.bot.portfolio_manager.get_portfolio_summary()
        assert portfolio_summary['active_positions'] > 0
    
    @pytest.mark.asyncio
    async def test_trading_enable_disable(self):
        """Trading aktif/deaktif testi"""
        await self.bot.initialize()
        
        # İlk başta aktif olmalı
        assert self.bot.is_trading_enabled is True
        
        # Deaktif et
        self.bot.disable_trading()
        assert self.bot.is_trading_enabled is False
        
        # Trade denendiğinde reject olmalı
        result = await self.bot.execute_trade('BTC/USDT', 'BUY', 0.1, 50000.0)
        assert result['success'] is False
        assert 'disabled' in result['message'].lower()
        
        # Tekrar aktif et
        self.bot.enable_trading()
        assert self.bot.is_trading_enabled is True
    
    @pytest.mark.asyncio
    async def test_market_opportunities(self):
        """Piyasa fırsatları testi"""
        await self.bot.initialize()
        
        opportunities = await self.bot.get_market_opportunities()
        
        assert isinstance(opportunities, list)
        # En fazla 5 fırsat dönmeli
        assert len(opportunities) <= 5
        
        # Her fırsat gerekli alanları içermeli
        for opp in opportunities:
            assert 'symbol' in opp
            assert 'action' in opp
            assert 'confidence' in opp
            assert 'target_price' in opp
    
    @pytest.mark.asyncio
    async def test_daily_report_generation(self):
        """Günlük rapor testi"""
        await self.bot.initialize()
        
        # Bir trade ekle
        await self.bot.execute_trade('ETH/USDT', 'BUY', 1.0, 3000.0)
        
        report = self.bot.get_daily_report()
        
        assert 'date' in report
        assert 'portfolio_value' in report
        assert 'daily_return' in report
        assert 'total_return' in report
        assert 'trades_today' in report
        assert 'bot_status' in report
        
        assert report['portfolio_value'] > 0
        assert report['trades_today'] >= 1
    
    @pytest.mark.asyncio
    async def test_emergency_stop(self):
        """Acil durum durdurma testi"""
        await self.bot.initialize()
        
        # Önce bir pozisyon aç
        await self.bot.execute_trade('BTC/USDT', 'BUY', 0.1, 50000.0)
        
        # Pozisyon olduğunu doğrula
        portfolio_before = self.bot.portfolio_manager.get_portfolio_summary()
        assert portfolio_before['active_positions'] > 0
        
        # Emergency stop
        result = await self.bot.emergency_stop()
        
        assert 'closed_positions' in result
        assert result['closed_positions'] >= 1
        assert not self.bot.is_trading_enabled
        
        # Portfolio'da pozisyon kalmamalı
        portfolio_after = self.bot.portfolio_manager.get_portfolio_summary()
        assert portfolio_after['active_positions'] == 0
    
    def test_error_handling(self):
        """Hata yönetimi testi"""
        # Geçersiz trade parametreleri
        bot = SmartInvestmentBot(initial_capital=-1000.0)  # Negatif sermaye
        
        # Bot başlatma başarısız olmamalı ama uyarı vermeli
        # (defensive programming)
        assert bot.initial_capital == -1000.0  # Değer korunmalı
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self):
        """Performans takip testi"""
        await self.bot.initialize()
        
        # Birkaç trade yap
        trades = [
            ('BTC/USDT', 'BUY', 0.1, 50000, 100),    # +$100
            ('ETH/USDT', 'BUY', 1.0, 3000, -50),     # -$50
            ('AAPL', 'BUY', 10, 150, 75)             # +$75
        ]
        
        for symbol, action, amount, price, pnl in trades:
            # Profit/loss'u manuel olarak profit calculator'a kaydet
            self.bot.profit_calculator.record_trade(
                action, symbol, amount, price, 
                exit_price=price + (pnl/amount),
                profit_loss=pnl
            )
        
        # Performance summary kontrol
        summary = self.bot.profit_calculator.get_performance_summary()
        
        assert summary['total_trades'] == 3
        assert summary['total_profit'] == 125.0  # 100 - 50 + 75
        assert summary['win_rate'] == 2/3  # 2 kazançlı, 1 zararlı
        assert summary['current_capital'] == 10125.0


class TestBotComponents:
    """Bot bileşenleri ayrı testleri"""
    
    @pytest.mark.asyncio
    async def test_api_client_initialization(self):
        """API client başlatma testi"""
        bot = SmartInvestmentBot(10000.0)
        await bot.initialize()
        
        # API client'lar placeholder olarak başlatılmalı
        assert 'binance' in bot.api_clients
        assert 'yahoo_finance' in bot.api_clients
        assert 'alpha_vantage' in bot.api_clients
    
    @pytest.mark.asyncio
    async def test_strategy_initialization(self):
        """Strateji başlatma testi"""
        bot = SmartInvestmentBot(10000.0)
        await bot.initialize()
        
        # Stratejiler placeholder olarak başlatılmalı
        assert 'scalping' in bot.strategies
        assert 'swing' in bot.strategies
    
    @pytest.mark.asyncio
    async def test_analysis_tools_initialization(self):
        """Analiz araçları başlatma testi"""
        bot = SmartInvestmentBot(10000.0)
        await bot.initialize()
        
        # Analiz araçları placeholder olarak başlatılmalı
        assert 'technical' in bot.analysis_tools
        assert 'scanner' in bot.analysis_tools
        assert 'sentiment' in bot.analysis_tools


@pytest.mark.asyncio
async def test_bot_lifecycle():
    """Bot yaşam döngüsü testi"""
    bot = SmartInvestmentBot(10000.0)
    
    # Initialize
    init_success = await bot.initialize()
    assert init_success is True
    assert not bot.is_running
    
    # Start bot (kısa süre için)
    start_task = asyncio.create_task(bot.start())
    
    # Biraz bekle
    await asyncio.sleep(0.1)
    assert bot.is_running
    
    # Stop bot
    await bot.stop()
    assert not bot.is_running
    
    # Task tamamlanana kadar bekle
    try:
        await asyncio.wait_for(start_task, timeout=1.0)
    except asyncio.TimeoutError:
        pass  # Expected if task is still running


if __name__ == '__main__':
    pytest.main([__file__, '-v'])