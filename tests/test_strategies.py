"""
Test for Trading Strategies
Unit tests for scalping and swing strategies
"""

import pytest
import sys
import os
import numpy as np
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from strategies.base_strategy import BaseStrategy, Signal, SignalType
from strategies.scalping_strategy import ScalpingStrategy
from strategies.swing_strategy import SwingStrategy


def create_mock_historical_data(length=100, base_price=50000, volatility=0.02):
    """Mock historical data oluşturma"""
    data = []
    current_price = base_price
    
    for i in range(length):
        # Random price movement
        change = np.random.uniform(-volatility, volatility)
        current_price *= (1 + change)
        
        # OHLCV data
        open_price = current_price * (1 + np.random.uniform(-0.001, 0.001))
        high_price = max(open_price, current_price) * (1 + np.random.uniform(0, 0.005))
        low_price = min(open_price, current_price) * (1 - np.random.uniform(0, 0.005))
        volume = np.random.uniform(1000000, 5000000)
        
        data.append({
            'timestamp': datetime.now() - timedelta(hours=length-i),
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': current_price,
            'volume': volume
        })
    
    return data


class TestBaseStrategy:
    """Base strategy test sınıfı"""
    
    def setup_method(self):
        """Test setup"""
        # Concrete strategy for testing abstract base
        class TestStrategy(BaseStrategy):
            async def analyze(self, symbol, historical_data, current_price, **kwargs):
                return Signal(symbol, SignalType.BUY, 0.8, current_price)
            
            def get_risk_parameters(self, signal):
                return {
                    'stop_loss_price': signal.price * 0.98,
                    'take_profit_price': signal.price * 1.02,
                    'position_size_percentage': 0.05
                }
        
        self.strategy = TestStrategy("TestStrategy", "1h")
    
    def test_strategy_initialization(self):
        """Strateji başlatma testi"""
        assert self.strategy.name == "TestStrategy"
        assert self.strategy.timeframe == "1h"
        assert self.strategy.is_active is True
        assert self.strategy.min_confidence == 0.6
        assert self.strategy.signals_generated == 0
    
    @pytest.mark.asyncio
    async def test_signal_generation(self):
        """Sinyal üretme testi"""
        historical_data = create_mock_historical_data(50)
        current_price = 50000.0
        
        signal = await self.strategy.analyze("BTC/USDT", historical_data, current_price)
        
        assert signal is not None
        assert signal.symbol == "BTC/USDT"
        assert signal.signal_type == SignalType.BUY
        assert signal.confidence == 0.8
        assert signal.price == current_price
    
    def test_signal_validation(self):
        """Sinyal doğrulama testi"""
        # Valid signal
        valid_signal = Signal("BTC/USDT", SignalType.BUY, 0.8, 50000.0)
        assert self.strategy.validate_signal(valid_signal) is True
        
        # Invalid signals
        low_confidence_signal = Signal("BTC/USDT", SignalType.BUY, 0.3, 50000.0)
        assert self.strategy.validate_signal(low_confidence_signal) is False
        
        zero_price_signal = Signal("BTC/USDT", SignalType.BUY, 0.8, 0.0)
        assert self.strategy.validate_signal(zero_price_signal) is False
        
        # Old signal
        old_signal = Signal("BTC/USDT", SignalType.BUY, 0.8, 50000.0, 
                           datetime.now() - timedelta(hours=2))
        assert self.strategy.validate_signal(old_signal) is False
    
    def test_performance_tracking(self):
        """Performans takip testi"""
        signal = Signal("BTC/USDT", SignalType.BUY, 0.8, 50000.0)
        
        # Başarılı trade
        self.strategy.update_performance(signal, executed=True, profit=100.0)
        
        assert self.strategy.signals_generated == 1
        assert self.strategy.signals_executed == 1
        assert self.strategy.successful_signals == 1
        assert self.strategy.total_profit == 100.0
        
        # Başarısız trade
        self.strategy.update_performance(signal, executed=True, profit=-50.0)
        
        assert self.strategy.signals_generated == 2
        assert self.strategy.signals_executed == 2
        assert self.strategy.successful_signals == 1  # Hala 1
        assert self.strategy.total_profit == 50.0     # 100 - 50
    
    def test_position_size_calculation(self):
        """Position size hesaplama testi"""
        capital = 10000.0
        risk_percentage = 0.02
        
        signal = Signal("BTC/USDT", SignalType.BUY, 0.8, 50000.0)
        
        position_size = self.strategy.calculate_position_size(capital, risk_percentage, signal)
        
        # Base size: 10000 * 0.02 = 200
        # Confidence multiplier: 1 + 0.8 = 1.8
        # Expected: 200 * 1.8 = 360
        expected = 360.0
        assert abs(position_size - expected) < 1.0
    
    def test_execution_decision(self):
        """Sinyal çalıştırma kararı testi"""
        signal = Signal("BTC/USDT", SignalType.BUY, 0.8, 50000.0)
        
        # Normal koşullar - çalıştırılmalı
        decision = self.strategy.should_execute_signal(signal, {}, 0.05)
        assert decision['should_execute'] is True
        
        # Yüksek portföy riski - çalıştırılmamalı
        decision = self.strategy.should_execute_signal(signal, {}, 0.20)
        assert decision['should_execute'] is False
        assert 'risk too high' in decision['reason'].lower()
        
        # Strateji deaktif - çalıştırılmamalı
        self.strategy.disable()
        decision = self.strategy.should_execute_signal(signal, {}, 0.05)
        assert decision['should_execute'] is False
        assert 'disabled' in decision['reason'].lower()


class TestScalpingStrategy:
    """Scalping strategy test sınıfı"""
    
    def setup_method(self):
        """Test setup"""
        self.strategy = ScalpingStrategy(timeframe='5m')
    
    def test_scalping_parameters(self):
        """Scalping parametreleri testi"""
        assert self.strategy.name == "Scalping"
        assert self.strategy.timeframe == "5m"
        assert self.strategy.parameters['rsi_oversold'] == 30
        assert self.strategy.parameters['rsi_overbought'] == 70
        assert self.strategy.parameters['stop_loss_pct'] == 0.005
        assert self.strategy.parameters['take_profit_pct'] == 0.010
    
    @pytest.mark.asyncio
    async def test_scalping_analysis(self):
        """Scalping analizi testi"""
        # Oversold koşulu için data
        historical_data = create_mock_historical_data(30, base_price=50000, volatility=0.01)
        
        # Mock RSI oversold koşulu simüle et
        # Son fiyatı düşük yap ki RSI düşük olsun
        for i in range(5):
            historical_data[-i-1]['close'] *= 0.99  # %1 düşüş
        
        current_price = historical_data[-1]['close']
        
        signal = await self.strategy.analyze("BTC/USDT", historical_data, current_price)
        
        # Koşullar sağlanmadığı için sinyal çıkmayabilir (bu normal)
        # Test sadece crash etmediğini doğrular
        if signal:
            assert signal.symbol == "BTC/USDT"
            assert signal.confidence >= self.strategy.min_confidence
    
    def test_risk_parameters(self):
        """Scalping risk parametreleri testi"""
        signal = Signal("BTC/USDT", SignalType.BUY, 0.8, 50000.0)
        
        risk_params = self.strategy.get_risk_parameters(signal)
        
        assert 'stop_loss_price' in risk_params
        assert 'take_profit_price' in risk_params
        assert 'position_size_percentage' in risk_params
        
        # BUY sinyali için
        assert risk_params['stop_loss_price'] < signal.price
        assert risk_params['take_profit_price'] > signal.price
        
        # Stop loss: 50000 * (1 - 0.005) = 49750
        expected_sl = 50000.0 * (1 - 0.005)
        assert abs(risk_params['stop_loss_price'] - expected_sl) < 1.0
        
        # Take profit: 50000 * (1 + 0.010) = 50500
        expected_tp = 50000.0 * (1 + 0.010)
        assert abs(risk_params['take_profit_price'] - expected_tp) < 1.0
    
    def test_market_condition_adjustment(self):
        """Piyasa koşulu ayarlama testi"""
        original_stop_loss = self.strategy.parameters['stop_loss_pct']
        
        # Yüksek volatilite
        self.strategy.adjust_for_market_conditions(
            market_volatility=0.05,  # %5 volatilite
            trading_volume=2.5
        )
        
        # Daha muhafazakar parametreler beklenir
        assert self.strategy.parameters['stop_loss_pct'] < original_stop_loss
        
    def test_ideal_symbols_selection(self):
        """İdeal semboller seçimi testi"""
        available_symbols = ['BTC/USDT', 'ETH/USDT', 'DOGE/USDT']
        
        symbol_data = {
            'BTC/USDT': {
                'volume': 2000000,      # Yüksek volume
                'volatility': 0.02,     # İdeal volatilite
                'spread_pct': 0.0005    # Düşük spread
            },
            'ETH/USDT': {
                'volume': 500000,       # Düşük volume
                'volatility': 0.03,     # Yüksek volatilite
                'spread_pct': 0.002     # Yüksek spread
            },
            'DOGE/USDT': {
                'volume': 3000000,      # Çok yüksek volume
                'volatility': 0.08,     # Çok yüksek volatilite
                'spread_pct': 0.0008    # Düşük spread
            }
        }
        
        ideal_symbols = self.strategy.get_ideal_symbols(available_symbols, symbol_data)
        
        # BTC en ideal olmalı (balanced metrics)
        assert 'BTC/USDT' in ideal_symbols
        assert isinstance(ideal_symbols, list)


class TestSwingStrategy:
    """Swing strategy test sınıfı"""
    
    def setup_method(self):
        """Test setup"""
        self.strategy = SwingStrategy(timeframe='4h')
    
    def test_swing_parameters(self):
        """Swing parametreleri testi"""
        assert self.strategy.name == "Swing"
        assert self.strategy.timeframe == "4h"
        assert self.strategy.parameters['ema_short'] == 12
        assert self.strategy.parameters['ema_long'] == 26
        assert self.strategy.parameters['stop_loss_pct'] == 0.03
        assert self.strategy.parameters['take_profit_pct'] == 0.08
    
    @pytest.mark.asyncio
    async def test_swing_analysis(self):
        """Swing analizi testi"""
        historical_data = create_mock_historical_data(60, base_price=50000, volatility=0.01)
        current_price = historical_data[-1]['close']
        
        signal = await self.strategy.analyze("BTC/USDT", historical_data, current_price)
        
        # Analysis crash etmemeli
        if signal:
            assert signal.symbol == "BTC/USDT"
            assert 'strategy_type' in signal.metadata
            assert signal.metadata['strategy_type'] == 'swing'
    
    def test_market_structure_analysis(self):
        """Market structure analizi testi"""
        # Uptrend data oluştur
        uptrend_data = []
        base_price = 45000
        
        for i in range(50):
            # Genel uptrend with noise
            trend_price = base_price * (1 + (i * 0.002))  # %0.2 günlük artış
            noise = np.random.uniform(-0.01, 0.01)
            price = trend_price * (1 + noise)
            
            uptrend_data.append({
                'timestamp': datetime.now() - timedelta(hours=50-i),
                'open': price * 0.999,
                'high': price * 1.002,
                'low': price * 0.998,
                'close': price,
                'volume': np.random.uniform(1000000, 2000000)
            })
        
        structure = self.strategy.analyze_market_structure(uptrend_data)
        
        assert 'structure' in structure
        assert 'swing_highs' in structure
        assert 'swing_lows' in structure
        
        # Uptrend detect edilmeli
        assert structure['structure'] in ['uptrend', 'sideways']  # Noise'dan dolayı sideways da olabilir
    
    def test_support_resistance_calculation(self):
        """Support/resistance hesaplama testi"""
        historical_data = create_mock_historical_data(50)
        
        closes = [d['close'] for d in historical_data]
        highs = [d['high'] for d in historical_data]
        lows = [d['low'] for d in historical_data]
        
        sr_levels = self.strategy._find_support_resistance(highs, lows, closes)
        
        assert 'support' in sr_levels
        assert 'resistance' in sr_levels
        assert sr_levels['support'] > 0
        assert sr_levels['resistance'] > sr_levels['support']
    
    def test_optimal_entry_calculation(self):
        """Optimal entry hesaplama testi"""
        signal = Signal("BTC/USDT", SignalType.BUY, 0.8, 50000.0)
        support_resistance = {'support': 49500.0, 'resistance': 50500.0}
        
        entry_info = self.strategy.calculate_optimal_entry(signal, support_resistance)
        
        assert 'entry_price' in entry_info
        assert 'entry_type' in entry_info
        
        # BUY sinyali için support yakınında giriş olmalı
        assert entry_info['entry_price'] <= signal.price
        assert entry_info['entry_price'] >= support_resistance['support']
    
    def test_swing_opportunities(self):
        """Swing fırsatları testi"""
        symbols_data = {
            'BTC/USDT': {
                'historical_data': create_mock_historical_data(60),
                'current_price': 50000.0
            },
            'ETH/USDT': {
                'historical_data': create_mock_historical_data(60, base_price=3000),
                'current_price': 3000.0
            }
        }
        
        opportunities = self.strategy.get_swing_opportunities(symbols_data)
        
        assert isinstance(opportunities, list)
        assert len(opportunities) <= 5  # Max 5 opportunity
        
        for opp in opportunities:
            assert 'symbol' in opp
            assert 'reversal_score' in opp
            assert 'market_structure' in opp


class TestStrategyPerformance:
    """Strateji performans testleri"""
    
    def test_performance_metrics(self):
        """Performans metrikleri testi"""
        strategy = ScalpingStrategy()
        
        # Mock performance data
        signal1 = Signal("BTC/USDT", SignalType.BUY, 0.8, 50000.0)
        signal2 = Signal("ETH/USDT", SignalType.SELL, 0.7, 3000.0)
        
        strategy.update_performance(signal1, executed=True, profit=100.0)
        strategy.update_performance(signal2, executed=True, profit=-50.0)
        strategy.update_performance(signal1, executed=False, profit=0.0)  # Rejected
        
        metrics = strategy.get_performance_metrics()
        
        assert metrics['signals_generated'] == 3
        assert metrics['signals_executed'] == 2
        assert metrics['successful_signals'] == 1
        assert metrics['win_rate'] == 0.5  # 1/2
        assert metrics['execution_rate'] == 2/3  # 2/3
        assert metrics['total_profit'] == 50.0
    
    def test_strategy_enable_disable(self):
        """Strateji aktif/deaktif testi"""
        strategy = ScalpingStrategy()
        
        assert strategy.is_active is True
        
        strategy.disable()
        assert strategy.is_active is False
        
        strategy.enable()
        assert strategy.is_active is True
    
    def test_parameter_updates(self):
        """Parametre güncelleme testi"""
        strategy = SwingStrategy()
        
        original_stop_loss = strategy.parameters['stop_loss_pct']
        
        strategy.set_parameter('stop_loss_pct', 0.05)
        
        assert strategy.parameters['stop_loss_pct'] == 0.05
        assert strategy.parameters['stop_loss_pct'] != original_stop_loss


class TestTechnicalIndicators:
    """Teknik indikatör testleri"""
    
    def test_rsi_calculation(self):
        """RSI hesaplama testi"""
        strategy = ScalpingStrategy()
        
        # Test data - trending up
        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
                 111, 112, 113, 114, 115, 116, 117, 118, 119, 120]
        
        rsi = strategy._calculate_rsi(prices, period=14)
        
        # Uptrend'de RSI yüksek olmalı
        assert rsi > 50
        assert 0 <= rsi <= 100
    
    def test_sma_calculation(self):
        """SMA hesaplama testi"""
        strategy = ScalpingStrategy()
        
        prices = [100, 102, 104, 106, 108]
        sma = strategy._calculate_sma(prices, period=5)
        
        expected = sum(prices) / len(prices)  # 104
        assert abs(sma - expected) < 0.01
    
    def test_stochastic_calculation(self):
        """Stochastic hesaplama testi"""
        strategy = ScalpingStrategy()
        
        # Test data
        highs = [105, 107, 109, 111, 113, 115, 117, 119, 121, 123, 125,
                127, 129, 131, 133, 135]
        lows = [95, 97, 99, 101, 103, 105, 107, 109, 111, 113, 115,
               117, 119, 121, 123, 125]
        closes = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120,
                 122, 124, 126, 128, 130]
        
        k_percent, d_percent = strategy._calculate_stochastic(highs, lows, closes, 14)
        
        assert 0 <= k_percent <= 100
        assert 0 <= d_percent <= 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])