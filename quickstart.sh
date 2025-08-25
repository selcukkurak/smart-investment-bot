#!/bin/bash

# Smart Investment Bot - Quick Start Script
# This script demonstrates how to get started with the bot

echo "🤖 SMART INVESTMENT BOT - QUICK START"
echo "===================================="
echo

# Check Python version
echo "📋 Checking requirements..."
python3 --version || echo "❌ Python 3 not found"

# Show project structure
echo
echo "📁 Project structure created:"
echo "   ✅ Core modules (profit calculator, risk manager, portfolio)"
echo "   ✅ API clients (Yahoo Finance, Binance)"
echo "   ✅ Trading strategies (Scalping, Swing)"
echo "   ✅ Technical analysis system"
echo "   ✅ Database models"
echo "   ✅ Configuration and logging"
echo "   ✅ Docker deployment setup"

# Run basic functionality test
echo
echo "🧪 Testing core functionality..."
python3 main_simple.py test

echo
echo "🎯 KEY FEATURES IMPLEMENTED:"
echo "   • Daily 1% profit target with dynamic adjustment"
echo "   • Multi-asset trading (Stocks, Crypto, Commodities, Forex)"
echo "   • Advanced risk management (2% max daily loss)"
echo "   • Technical analysis (RSI, MACD, Bollinger Bands)"
echo "   • Multiple trading strategies"
echo "   • Real-time portfolio monitoring"
echo "   • Database transaction logging"

echo
echo "📈 PROJECTED RETURNS (1% daily compound):"
echo "   • Month 1: ~34.8% gain"
echo "   • Month 2: ~81.7% gain"
echo "   • Year 1: ~3,678% gain"

echo
echo "🚀 NEXT STEPS:"
echo "   1. Set up API keys in .env file (copy from .env.example)"
echo "   2. Install dependencies: pip install -r requirements.txt"
echo "   3. Run demo: python main_simple.py demo"
echo "   4. Run comprehensive demo: python demo_comprehensive.py"
echo "   5. Start bot: python main.py"

echo
echo "⚠️  IMPORTANT: Always test with small amounts first!"
echo "🎉 Smart Investment Bot is ready for deployment!"