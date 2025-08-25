"""
Smart Investment Bot - Logging System
Centralized logging with file and console output
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class BotLogger:
    """
    Custom logger for the Smart Investment Bot
    """
    
    def __init__(self, name: str = "SmartBot", log_file: str = "logs/smart_bot.log", 
                 level: str = "INFO"):
        self.name = name
        self.log_file = log_file
        self.level = getattr(logging, level.upper(), logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path(log_file).parent
        log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(self.level)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str, extra_data: Optional[dict] = None):
        """Log info message"""
        if extra_data:
            message = f"{message} | {extra_data}"
        self.logger.info(message)
    
    def warning(self, message: str, extra_data: Optional[dict] = None):
        """Log warning message"""
        if extra_data:
            message = f"{message} | {extra_data}"
        self.logger.warning(message)
    
    def error(self, message: str, extra_data: Optional[dict] = None):
        """Log error message"""
        if extra_data:
            message = f"{message} | {extra_data}"
        self.logger.error(message)
    
    def debug(self, message: str, extra_data: Optional[dict] = None):
        """Log debug message"""
        if extra_data:
            message = f"{message} | {extra_data}"
        self.logger.debug(message)
    
    def critical(self, message: str, extra_data: Optional[dict] = None):
        """Log critical message"""
        if extra_data:
            message = f"{message} | {extra_data}"
        self.logger.critical(message)
    
    def log_trade(self, action: str, symbol: str, quantity: float, 
                 price: float, success: bool, reason: str = ""):
        """Log trading action"""
        status = "SUCCESS" if success else "FAILED"
        message = f"TRADE {status}: {action} {quantity} {symbol} @ {price}"
        if reason:
            message += f" | Reason: {reason}"
        
        if success:
            self.info(message)
        else:
            self.error(message)
    
    def log_signal(self, strategy: str, symbol: str, signal_type: str, 
                  confidence: float, reasoning: str):
        """Log trading signal"""
        message = f"SIGNAL: {strategy} | {symbol} | {signal_type} | Confidence: {confidence:.2f} | {reasoning}"
        self.info(message)
    
    def log_performance(self, daily_return: float, target: float, 
                       total_return: float, balance: float):
        """Log daily performance"""
        target_met = "✓" if daily_return >= target else "✗"
        message = f"PERFORMANCE: Daily return: {daily_return:.2f}% {target_met} | Target: {target:.2f}% | Total: {total_return:.2f}% | Balance: ${balance:.2f}"
        self.info(message)
    
    def log_risk_event(self, event_type: str, details: str, severity: str = "WARNING"):
        """Log risk management events"""
        message = f"RISK {severity}: {event_type} | {details}"
        if severity == "CRITICAL":
            self.critical(message)
        elif severity == "ERROR":
            self.error(message)
        else:
            self.warning(message)
    
    def log_api_error(self, api_name: str, action: str, error: str):
        """Log API errors"""
        message = f"API ERROR: {api_name} | {action} | {error}"
        self.error(message)
    
    def log_system_event(self, event: str, details: str = ""):
        """Log system events (startup, shutdown, etc.)"""
        message = f"SYSTEM: {event}"
        if details:
            message += f" | {details}"
        self.info(message)


# Global logger instance
bot_logger = BotLogger()