"""
Smart Investment Bot - Main Application Entry Point
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from core.bot import SmartInvestmentBot, TradingMode
from utils.config import ConfigManager
from utils.logger import setup_logging, get_logger
from utils.notifications import NotificationManager
from database.database import DatabaseManager


async def main():
    """Ana uygulama fonksiyonu"""
    
    # Configuration yükleme
    config_manager = ConfigManager()
    if not await config_manager.load_config():
        print("❌ Configuration load failed")
        return
    
    # Logging kurulumu
    logging_config = config_manager.get('logging', {})
    if not setup_logging(logging_config):
        print("❌ Logging setup failed")
        return
    
    logger = get_logger('Main')
    logger.info("🚀 Starting Smart Investment Bot...")
    
    try:
        # Database başlatma
        db_url = config_manager.get('database.url')
        db_manager = DatabaseManager(db_url)
        
        if not await db_manager.initialize():
            logger.error("❌ Database initialization failed")
            return
        
        # Bot başlatma
        initial_capital = config_manager.get('bot.initial_capital', 10000.0)
        trading_mode_str = config_manager.get('bot.trading_mode', 'paper')
        
        try:
            trading_mode = TradingMode(trading_mode_str)
        except ValueError:
            trading_mode = TradingMode.PAPER
            logger.warning(f"Invalid trading mode '{trading_mode_str}', using PAPER mode")
        
        bot = SmartInvestmentBot(initial_capital, trading_mode)
        
        if not await bot.initialize():
            logger.error("❌ Bot initialization failed")
            return
        
        # Notification manager başlatma
        notification_config = config_manager.get('notifications', {})
        notification_manager = NotificationManager(notification_config)
        
        # Startup bildirimi
        await notification_manager.send_startup_notification()
        
        # Notification service başlatma
        notification_task = asyncio.create_task(
            notification_manager.start_notification_service()
        )
        
        logger.info("✅ All systems initialized successfully")
        logger.info(f"💰 Initial capital: ${initial_capital:,.2f}")
        logger.info(f"📊 Trading mode: {trading_mode.value}")
        
        # Bot'u başlatma
        bot_task = asyncio.create_task(bot.start())
        
        # Graceful shutdown için signal handling
        import signal
        
        def signal_handler(signum, frame):
            logger.info("🔴 Shutdown signal received")
            asyncio.create_task(shutdown(bot, notification_manager, db_manager))
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Wait for bot to finish
        await bot_task
        
    except KeyboardInterrupt:
        logger.info("🔴 Shutdown requested by user")
    except Exception as e:
        logger.error(f"❌ Application error: {str(e)}")
    finally:
        # Cleanup
        if 'bot' in locals():
            await shutdown(bot, notification_manager if 'notification_manager' in locals() else None, 
                          db_manager if 'db_manager' in locals() else None)


async def shutdown(bot, notification_manager, db_manager):
    """Graceful shutdown"""
    logger = get_logger('Main')
    logger.info("🔄 Starting graceful shutdown...")
    
    try:
        # Bot'u durdur
        if bot and bot.is_running:
            await bot.stop()
        
        # Performance summary al
        if bot:
            performance_summary = bot.portfolio_manager.get_performance_metrics()
            
            # Shutdown bildirimi gönder
            if notification_manager:
                await notification_manager.send_shutdown_notification(performance_summary)
                await notification_manager.stop_notification_service()
        
        # Database bağlantısını kapat
        if db_manager:
            await db_manager.close()
        
        logger.info("✅ Graceful shutdown completed")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {str(e)}")


def create_example_files():
    """Örnek konfigürasyon dosyalarını oluşturma"""
    config_manager = ConfigManager()
    
    # Create config directory
    os.makedirs('config', exist_ok=True)
    
    # Create example config
    config_manager.create_example_config()
    
    # Create .env.example
    env_example = """
# Smart Investment Bot Environment Variables
# Copy this file to .env and update with your settings

# Binance API (for crypto trading)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# Alpha Vantage API (for forex/stocks)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# Database URL (optional, defaults to SQLite)
DATABASE_URL=sqlite+aiosqlite:///smart_investment_bot.db

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Discord Webhook (optional)
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here

# Bot Settings
BOT_INITIAL_CAPITAL=10000.0
BOT_TRADING_MODE=paper
BOT_MAX_POSITIONS=10

# Web Dashboard
WEB_HOST=0.0.0.0
WEB_PORT=8000
    """.strip()
    
    with open('.env.example', 'w') as f:
        f.write(env_example)
    
    print("📝 Example configuration files created:")
    print("  - config/config.example.yaml")
    print("  - .env.example")
    print("\n📋 Next steps:")
    print("  1. Copy config.example.yaml to config.yaml")
    print("  2. Copy .env.example to .env")
    print("  3. Update configuration files with your settings")
    print("  4. Run: python src/main.py")


if __name__ == '__main__':
    # Check if this is initial setup
    if len(sys.argv) > 1 and sys.argv[1] == 'setup':
        create_example_files()
    else:
        # Run bot
        print("🤖 Smart Investment Bot")
        print("=" * 50)
        
        if not os.path.exists('config/config.yaml') and not os.path.exists('.env'):
            print("⚠️  No configuration found!")
            print("Run: python src/main.py setup")
            print("Then configure your settings and run again.")
            sys.exit(1)
        
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n🔴 Bot stopped by user")
        except Exception as e:
            print(f"\n❌ Bot crashed: {str(e)}")
            sys.exit(1)