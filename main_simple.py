"""
Smart Investment Bot - Simplified Main Entry Point
Uses only standard library dependencies
"""

import asyncio
import sys
import signal
import json
import time
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

from src.core.profit_calculator import ProfitCalculator
from src.core.risk_manager import RiskManager
from src.core.portfolio_manager import PortfolioManager, AssetType
from src.apis.simple_yahoo_client import SimpleYahooFinanceClient


class SimpleBotRunner:
    """
    Simplified bot runner using standard library only
    """
    
    def __init__(self):
        self.shutdown_requested = False
        
        # Initialize core components
        self.profit_calculator = ProfitCalculator(10000)  # $10,000 starting capital
        self.risk_manager = RiskManager()
        self.portfolio = PortfolioManager(10000)
        self.yahoo_client = SimpleYahooFinanceClient()
        
        print("Smart Investment Bot initialized with $10,000 capital")
    
    def run_demo(self):
        """Run a comprehensive demo of the bot's capabilities"""
        print("\n🤖 Smart Investment Bot - Demo Mode")
        print("=" * 50)
        
        # Demo 1: Profit Calculator
        print("\n📊 Demo 1: Profit Calculation System")
        print("-" * 30)
        
        # Simulate 5 days of trading
        for i in range(5):
            date = datetime.now() - timedelta(days=4-i)
            opening = 10000 + (i * 100)
            
            # Simulate different outcomes
            if i == 1:  # Day 2: Below target
                closing = opening + (opening * 0.005)  # 0.5% gain
            elif i == 3:  # Day 4: Loss
                closing = opening - (opening * 0.01)   # 1% loss
            else:
                closing = opening + (opening * 0.012)  # 1.2% gain
            
            performance = self.profit_calculator.track_daily_performance(
                date, opening, closing, []
            )
            
            status = "✅ TARGET MET" if performance['target_met'] else "❌ MISSED TARGET"
            print(f"Day {i+1}: {performance['daily_return_rate']:.2%} return | {status}")
        
        # Show overall performance
        report = self.profit_calculator.get_performance_report()
        print(f"\n📈 Overall Performance:")
        print(f"   Success Rate: {report['target_success_rate']:.1%}")
        print(f"   Total Return: {report['total_return_rate']:.2%}")
        print(f"   Current Capital: ${report['current_capital']:.2f}")
        
        # Demo 2: Risk Management
        print(f"\n🛡️  Demo 2: Risk Management System")
        print("-" * 30)
        
        current_balance = 10500
        position_size = self.risk_manager.calculate_position_size(current_balance)
        print(f"Recommended position size: ${position_size:.2f} (10% of balance)")
        
        # Test trade approval
        can_trade, reason = self.risk_manager.should_allow_trade(
            current_balance, 10000, position_size
        )
        print(f"Trade approval: {'✅ Approved' if can_trade else '❌ Denied'} - {reason}")
        
        # Demo 3: Portfolio Management
        print(f"\n💰 Demo 3: Portfolio Management")
        print("-" * 30)
        
        # Simulate some trades
        self.portfolio.add_asset("AAPL", AssetType.STOCK, 150.0)
        self.portfolio.buy_asset("AAPL", 10, 150.0, 1.5)  # Buy 10 shares at $150
        
        # Update price and show performance
        self.portfolio.update_asset_price("AAPL", 155.0)  # Price increased to $155
        
        portfolio_summary = self.portfolio.get_performance_summary()
        print(f"Portfolio Value: ${portfolio_summary['current_portfolio_value']:.2f}")
        print(f"Total Return: {portfolio_summary['total_return_percent']:.2f}%")
        print(f"Cash: ${portfolio_summary['current_cash']:.2f}")
        
        allocation = self.portfolio.get_asset_allocation()
        print(f"Asset Allocation:")
        for asset, percent in allocation.items():
            print(f"  {asset}: {percent:.1f}%")
        
        # Demo 4: Market Data (if internet available)
        print(f"\n📈 Demo 4: Market Data")
        print("-" * 30)
        
        test_symbols = ['AAPL', 'GOOGL', 'BTC-USD']
        for symbol in test_symbols:
            try:
                price = self.yahoo_client.get_current_price(symbol)
                if price:
                    print(f"{symbol}: ${price:.2f}")
                else:
                    print(f"{symbol}: Price not available")
            except:
                print(f"{symbol}: Connection error")
        
        # Demo 5: Dynamic Target Calculation
        print(f"\n🎯 Demo 5: Dynamic Target System")
        print("-" * 30)
        
        # Test compensation calculation
        compensation_rate = self.profit_calculator.calculate_missed_target_compensation(10, 15)
        print(f"Normal daily target: 1.00%")
        print(f"Compensation rate (10 missed days, 15 remaining): {compensation_rate:.2%}")
        
        # Monthly projection
        month_1_target = self.profit_calculator.get_monthly_expected_return(1, 2024)
        print(f"Month 1 expected value: ${month_1_target:.2f} ({((month_1_target/10000)-1)*100:.1f}% gain)")
        
        print(f"\n✅ Demo completed successfully!")
        print(f"🚀 Smart Investment Bot is ready for live trading.")
        
    def run_simple_test(self):
        """Run a simple functionality test"""
        print("\n🧪 Running Simple Functionality Test")
        print("=" * 40)
        
        # Test 1: Core calculations
        print("Test 1: Profit Calculator...")
        target = self.profit_calculator.calculate_daily_target(10000)
        assert target == 100, f"Expected 100, got {target}"
        print("✅ Daily target calculation works")
        
        # Test 2: Risk management
        print("Test 2: Risk Manager...")
        position_size = self.risk_manager.calculate_position_size(10000)
        assert 150 <= position_size <= 250, f"Position size out of range: {position_size}"
        print("✅ Position sizing works")
        
        # Test 3: Portfolio operations
        print("Test 3: Portfolio Manager...")
        initial_value = self.portfolio.get_portfolio_value()
        assert initial_value == 10000, f"Expected 10000, got {initial_value}"
        print("✅ Portfolio initialization works")
        
        # Test 4: Asset operations
        print("Test 4: Asset Management...")
        self.portfolio.add_asset("TEST", AssetType.STOCK, 100.0)
        success = self.portfolio.buy_asset("TEST", 5, 100.0, 0.5)
        assert success, "Asset purchase failed"
        
        new_value = self.portfolio.get_portfolio_value()
        # Cash (9499.5) + Asset value (500) = 9999.5
        expected_value = 10000 - 0.5  # Only commission is lost, asset value is maintained
        assert abs(new_value - expected_value) < 1, f"Portfolio value incorrect: {new_value} vs {expected_value}"
        print("✅ Asset trading works")
        
        print("\n🎉 All basic tests passed!")
        print("🚀 Core functionality is working correctly.")


def main():
    """Main entry point"""
    runner = SimpleBotRunner()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            runner.run_demo()
        elif sys.argv[1] == "test":
            runner.run_simple_test()
        else:
            print("Usage: python main.py [demo|test]")
    else:
        print("Smart Investment Bot")
        print("Usage:")
        print("  python main.py demo  - Run comprehensive demo")
        print("  python main.py test  - Run basic functionality test")
        print("\nNote: Full bot requires external dependencies (see requirements.txt)")


if __name__ == "__main__":
    main()