"""
Smart Investment Bot - Main Entry Point
Command line interface and bot runner
"""

import asyncio
import sys
import signal
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

from src.core.bot import SmartInvestmentBot
from src.utils.logger import bot_logger
from src.utils.config import Config


class BotRunner:
    """
    Main runner for the Smart Investment Bot
    """
    
    def __init__(self):
        self.bot: Optional[SmartInvestmentBot] = None
        self.shutdown_requested = False
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        bot_logger.info("Shutdown signal received")
        self.shutdown_requested = True
        
        if self.bot:
            asyncio.create_task(self.bot.stop())
    
    async def run_bot(self, config_path: str = "config.yaml"):
        """Run the bot with given configuration"""
        try:
            # Initialize bot
            self.bot = SmartInvestmentBot(config_path)
            
            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            # Start bot
            await self.bot.start()
            
        except KeyboardInterrupt:
            bot_logger.info("Bot stopped by user")
        except Exception as e:
            bot_logger.error(f"Bot error: {e}")
        finally:
            if self.bot:
                await self.bot.stop()
    
    def run_demo(self):
        """Run a demo of the bot's capabilities"""
        bot_logger.log_system_event("Starting demo mode")
        
        # Initialize components for demonstration
        config = Config()
        
        # Demo the profit calculator
        from src.core.profit_calculator import ProfitCalculator
        profit_calc = ProfitCalculator(10000)
        
        # Simulate some daily performance
        from datetime import datetime, timedelta
        
        for i in range(5):
            date = datetime.now() - timedelta(days=4-i)
            opening = 10000 + (i * 100)
            closing = opening + (opening * 0.01)  # 1% gain
            
            performance = profit_calc.track_daily_performance(
                date, opening, closing, []
            )
            
            bot_logger.info(f"Demo Day {i+1}: {performance['daily_return_rate']:.2%} return")
        
        # Demo report
        report = profit_calc.get_performance_report()
        bot_logger.info(f"Demo Summary: {report['target_success_rate']:.1%} success rate")
        bot_logger.info(f"Total return: {report['total_return_rate']:.2%}")
        
        bot_logger.log_system_event("Demo completed")


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        runner = BotRunner()
        runner.run_demo()
    else:
        runner = BotRunner()
        asyncio.run(runner.run_bot())


if __name__ == "__main__":
    main()