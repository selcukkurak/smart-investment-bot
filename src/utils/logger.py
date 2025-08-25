"""
Logger - Logging sistemi
Structured logging with file rotation and multiple outputs
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Dict, Optional
import json


class ColoredFormatter(logging.Formatter):
    """Renkli terminal output formatter"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON format logging"""
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'message']:
                log_obj[key] = value
        
        return json.dumps(log_obj)


class LoggerManager:
    """
    Logging yönetim sınıfı
    
    Özellikler:
    - File rotation
    - Multiple output formats
    - Level-based filtering
    - Performance logging
    - Error tracking
    """
    
    def __init__(self, config: Dict = None):
        """
        Logger manager başlatma
        
        Args:
            config: Logging konfigürasyonu
        """
        self.config = config or {
            'level': 'INFO',
            'file_path': 'logs/bot.log',
            'max_file_size': '10MB',
            'backup_count': 5,
            'format': 'standard',
            'console_enabled': True,
            'file_enabled': True,
            'json_enabled': False
        }
        
        self.loggers = {}
        self.performance_logger = None
        
    def setup_logging(self) -> bool:
        """
        Logging sistemini kurma
        
        Returns:
            Kurulum başarılı mı
        """
        try:
            # Log directory oluştur
            log_dir = os.path.dirname(self.config['file_path'])
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            # Root logger configuration
            root_logger = logging.getLogger()
            root_logger.setLevel(getattr(logging, self.config['level'].upper()))
            
            # Clear existing handlers
            root_logger.handlers.clear()
            
            # Console handler
            if self.config.get('console_enabled', True):
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(logging.INFO)
                
                if self.config.get('format') == 'json':
                    console_formatter = JSONFormatter()
                else:
                    console_formatter = ColoredFormatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                
                console_handler.setFormatter(console_formatter)
                root_logger.addHandler(console_handler)
            
            # File handler with rotation
            if self.config.get('file_enabled', True):
                # Parse file size
                max_bytes = self._parse_file_size(self.config.get('max_file_size', '10MB'))
                backup_count = self.config.get('backup_count', 5)
                
                file_handler = logging.handlers.RotatingFileHandler(
                    self.config['file_path'],
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(logging.DEBUG)
                
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
                )
                file_handler.setFormatter(file_formatter)
                root_logger.addHandler(file_handler)
            
            # JSON file handler (optional)
            if self.config.get('json_enabled', False):
                json_file_path = self.config['file_path'].replace('.log', '.json')
                json_handler = logging.handlers.RotatingFileHandler(
                    json_file_path,
                    maxBytes=self._parse_file_size('50MB'),
                    backupCount=3,
                    encoding='utf-8'
                )
                json_handler.setLevel(logging.INFO)
                json_handler.setFormatter(JSONFormatter())
                root_logger.addHandler(json_handler)
            
            # Performance logger
            self._setup_performance_logger()
            
            # Test logging
            test_logger = self.get_logger('LoggerManager')
            test_logger.info("✅ Logging system initialized successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up logging: {str(e)}")
            return False
    
    def _parse_file_size(self, size_str: str) -> int:
        """Dosya boyutu string'ini byte'a çevirme"""
        size_str = size_str.upper()
        
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            # Assume bytes
            return int(size_str)
    
    def _setup_performance_logger(self) -> None:
        """Performance logging kurulumu"""
        self.performance_logger = logging.getLogger('Performance')
        
        # Separate performance log file
        perf_log_path = self.config['file_path'].replace('.log', '_performance.log')
        
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_log_path,
            maxBytes=self._parse_file_size('50MB'),
            backupCount=3,
            encoding='utf-8'
        )
        
        perf_formatter = JSONFormatter()
        perf_handler.setFormatter(perf_formatter)
        
        self.performance_logger.addHandler(perf_handler)
        self.performance_logger.setLevel(logging.INFO)
        self.performance_logger.propagate = False  # Don't propagate to root logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Named logger alma
        
        Args:
            name: Logger adı
            
        Returns:
            Logger instance
        """
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
            
        return self.loggers[name]
    
    def log_performance(self, operation: str, duration: float, 
                       success: bool, **kwargs) -> None:
        """
        Performance logging
        
        Args:
            operation: İşlem adı
            duration: Süre (saniye)
            success: Başarılı mı
            **kwargs: Ek bilgiler
        """
        if self.performance_logger:
            perf_data = {
                'operation': operation,
                'duration_seconds': duration,
                'success': success,
                'timestamp': datetime.now().isoformat(),
                **kwargs
            }
            
            self.performance_logger.info('', extra=perf_data)
    
    def log_trade_execution(self, trade_data: Dict) -> None:
        """
        Trade execution logging
        
        Args:
            trade_data: Trade bilgileri
        """
        trade_logger = self.get_logger('TradeExecution')
        
        trade_logger.info(
            f"🔄 {trade_data.get('trade_type', 'UNKNOWN')} "
            f"{trade_data.get('amount', 0)} {trade_data.get('symbol', 'UNKNOWN')} "
            f"at ${trade_data.get('price', 0):.4f} "
            f"(Strategy: {trade_data.get('strategy', 'manual')})",
            extra={
                'trade_type': trade_data.get('trade_type'),
                'symbol': trade_data.get('symbol'),
                'amount': trade_data.get('amount'),
                'price': trade_data.get('price'),
                'strategy': trade_data.get('strategy'),
                'profit_loss': trade_data.get('profit_loss'),
                'total_value': trade_data.get('total_value')
            }
        )
    
    def log_risk_event(self, event_type: str, symbol: str, 
                      risk_data: Dict) -> None:
        """
        Risk event logging
        
        Args:
            event_type: Risk event türü
            symbol: İlgili sembol
            risk_data: Risk bilgileri
        """
        risk_logger = self.get_logger('RiskManagement')
        
        risk_logger.warning(
            f"⚠️ Risk Event: {event_type} for {symbol}",
            extra={
                'event_type': event_type,
                'symbol': symbol,
                'risk_level': risk_data.get('risk_level'),
                'portfolio_risk': risk_data.get('portfolio_risk'),
                'position_risk': risk_data.get('position_risk')
            }
        )
    
    def log_signal_generation(self, signal_data: Dict) -> None:
        """
        Signal generation logging
        
        Args:
            signal_data: Sinyal bilgileri
        """
        signal_logger = self.get_logger('SignalGeneration')
        
        signal_logger.info(
            f"📊 Signal: {signal_data.get('signal_type', 'UNKNOWN')} "
            f"{signal_data.get('symbol', 'UNKNOWN')} "
            f"(Confidence: {signal_data.get('confidence', 0):.2%}, "
            f"Strategy: {signal_data.get('strategy', 'unknown')})",
            extra=signal_data
        )
    
    def log_api_call(self, api_name: str, endpoint: str, 
                    duration: float, success: bool, 
                    response_size: int = 0) -> None:
        """
        API call logging
        
        Args:
            api_name: API adı
            endpoint: Endpoint
            duration: İstek süresi
            success: Başarılı mı
            response_size: Response boyutu
        """
        api_logger = self.get_logger('APIClient')
        
        status_emoji = "✅" if success else "❌"
        
        api_logger.debug(
            f"{status_emoji} {api_name} API: {endpoint} "
            f"({duration:.3f}s, {response_size} bytes)",
            extra={
                'api_name': api_name,
                'endpoint': endpoint,
                'duration': duration,
                'success': success,
                'response_size': response_size
            }
        )
    
    def log_portfolio_update(self, portfolio_data: Dict) -> None:
        """
        Portfolio update logging
        
        Args:
            portfolio_data: Portfolio bilgileri
        """
        portfolio_logger = self.get_logger('Portfolio')
        
        portfolio_logger.info(
            f"💼 Portfolio Update: ${portfolio_data.get('total_value', 0):.2f} "
            f"({portfolio_data.get('total_return_pct', 0):+.2%}) "
            f"[{portfolio_data.get('active_positions', 0)} positions]",
            extra=portfolio_data
        )
    
    def create_trading_session_log(self, session_id: str) -> logging.Logger:
        """
        Trading session için özel logger
        
        Args:
            session_id: Session ID
            
        Returns:
            Session logger
        """
        session_logger = logging.getLogger(f'TradingSession.{session_id}')
        
        # Session-specific file handler
        session_log_path = self.config['file_path'].replace(
            '.log', f'_session_{session_id}.log'
        )
        
        session_handler = logging.FileHandler(session_log_path, encoding='utf-8')
        session_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        session_handler.setFormatter(session_formatter)
        session_logger.addHandler(session_handler)
        session_logger.setLevel(logging.INFO)
        session_logger.propagate = False
        
        return session_logger
    
    def get_log_statistics(self) -> Dict:
        """
        Log istatistikleri
        
        Returns:
            Log stats
        """
        stats = {
            'total_loggers': len(self.loggers),
            'log_file_path': self.config['file_path'],
            'log_level': self.config['level'],
            'handlers_configured': 0
        }
        
        # File size check
        if os.path.exists(self.config['file_path']):
            file_size = os.path.getsize(self.config['file_path'])
            stats['log_file_size_bytes'] = file_size
            stats['log_file_size_mb'] = file_size / (1024 * 1024)
        
        # Handler count
        root_logger = logging.getLogger()
        stats['handlers_configured'] = len(root_logger.handlers)
        
        return stats
    
    def set_log_level(self, level: str) -> bool:
        """
        Log level ayarlama
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            Ayarlama başarılı mı
        """
        try:
            numeric_level = getattr(logging, level.upper())
            
            # Update all loggers
            root_logger = logging.getLogger()
            root_logger.setLevel(numeric_level)
            
            for logger in self.loggers.values():
                logger.setLevel(numeric_level)
            
            self.config['level'] = level.upper()
            
            self.get_logger('LoggerManager').info(f"Log level changed to {level.upper()}")
            return True
            
        except AttributeError:
            return False
    
    def archive_logs(self) -> bool:
        """
        Log dosyalarını arşivleme
        
        Returns:
            Arşivleme başarılı mı
        """
        try:
            # Force log rotation
            root_logger = logging.getLogger()
            
            for handler in root_logger.handlers:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    handler.doRollover()
            
            self.get_logger('LoggerManager').info("Log files archived")
            return True
            
        except Exception as e:
            print(f"Error archiving logs: {str(e)}")
            return False
    
    def create_audit_logger(self) -> logging.Logger:
        """
        Audit trail için özel logger
        
        Returns:
            Audit logger
        """
        audit_logger = logging.getLogger('Audit')
        
        # Audit log file
        audit_log_path = self.config['file_path'].replace('.log', '_audit.log')
        
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_log_path,
            maxBytes=self._parse_file_size('100MB'),
            backupCount=10,
            encoding='utf-8'
        )
        
        # JSON format for audit logs
        audit_formatter = JSONFormatter()
        audit_handler.setFormatter(audit_formatter)
        
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)
        audit_logger.propagate = False
        
        return audit_logger
    
    def _parse_file_size(self, size_str: str) -> int:
        """Dosya boyutu parse etme"""
        size_str = size_str.upper()
        
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)


# Global logger instance
logger_manager = LoggerManager()


def setup_logging(config: Dict = None) -> bool:
    """
    Global logging setup
    
    Args:
        config: Logging konfigürasyonu
        
    Returns:
        Setup başarılı mı
    """
    global logger_manager
    
    if config:
        logger_manager.config.update(config)
    
    return logger_manager.setup_logging()


def get_logger(name: str) -> logging.Logger:
    """
    Named logger alma
    
    Args:
        name: Logger adı
        
    Returns:
        Logger instance
    """
    return logger_manager.get_logger(name)


def log_trade(trade_data: Dict) -> None:
    """Trade logging shortcut"""
    logger_manager.log_trade_execution(trade_data)


def log_performance(operation: str, duration: float, 
                   success: bool, **kwargs) -> None:
    """Performance logging shortcut"""
    logger_manager.log_performance(operation, duration, success, **kwargs)


def log_risk_event(event_type: str, symbol: str, risk_data: Dict) -> None:
    """Risk event logging shortcut"""
    logger_manager.log_risk_event(event_type, symbol, risk_data)