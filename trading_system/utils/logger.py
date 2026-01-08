"""Structured logging system."""
import sys
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
import structlog
from structlog.types import EventDict, Processor
import colorama


# Initialize colorama for cross-platform color support
colorama.init()


def add_timestamp(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add timestamp to log entries."""
    event_dict["timestamp"] = datetime.utcnow().isoformat()
    return event_dict


def add_log_level_color(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add color to log level for console output."""
    level = event_dict.get("level", "").upper()
    colors = {
        "DEBUG": colorama.Fore.CYAN,
        "INFO": colorama.Fore.GREEN,
        "WARNING": colorama.Fore.YELLOW,
        "ERROR": colorama.Fore.RED,
        "CRITICAL": colorama.Fore.RED + colorama.Style.BRIGHT,
    }
    if level in colors:
        event_dict["level"] = colors[level] + level + colorama.Style.RESET_ALL
    return event_dict


class TradingLogger:
    """Enhanced logging system for trading operations."""
    
    def __init__(
        self,
        name: str = "trading_system",
        log_file: Optional[Path] = None,
        log_level: str = "INFO",
        console_output: bool = True,
    ):
        """
        Initialize the trading logger.
        
        Args:
            name: Logger name
            log_file: Path to log file
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_output: Enable console output
        """
        self.name = name
        self.log_level = getattr(logging, log_level.upper())
        
        # Configure structlog
        processors: list[Processor] = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            add_timestamp,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ]
        
        if console_output:
            processors.append(add_log_level_color)
            
        # Add JSON formatter for file output
        if log_file:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())
            
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Setup standard library logging
        self._setup_stdlib_logging(log_file, console_output)
        
        # Get structured logger
        self.logger = structlog.get_logger(name)
        
    def _setup_stdlib_logging(self, log_file: Optional[Path], console_output: bool) -> None:
        """Setup standard library logging handlers."""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            root_logger.addHandler(console_handler)
            
        # File handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(self.log_level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, **kwargs)
        
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, **kwargs)
        
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, **kwargs)
        
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, **kwargs)
        
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, **kwargs)
        
    def trade(self, action: str, symbol: str, volume: float, price: float, **kwargs) -> None:
        """Log trading action."""
        self.logger.info(
            "trade_action",
            action=action,
            symbol=symbol,
            volume=volume,
            price=price,
            **kwargs
        )
        
    def order(self, order_type: str, symbol: str, volume: float, price: float, **kwargs) -> None:
        """Log order submission."""
        self.logger.info(
            "order_submitted",
            order_type=order_type,
            symbol=symbol,
            volume=volume,
            price=price,
            **kwargs
        )
        
    def performance(self, metric: str, value: float, **kwargs) -> None:
        """Log performance metric."""
        self.logger.info(
            "performance_metric",
            metric=metric,
            value=value,
            **kwargs
        )
        
    def latency(self, operation: str, latency_ms: float, **kwargs) -> None:
        """Log operation latency."""
        self.logger.debug(
            "latency_measurement",
            operation=operation,
            latency_ms=latency_ms,
            **kwargs
        )


# Global logger instance
_logger: Optional[TradingLogger] = None


def get_logger(
    name: str = "trading_system",
    log_file: Optional[Path] = None,
    log_level: str = "INFO",
) -> TradingLogger:
    """Get or create the global logger instance."""
    global _logger
    if _logger is None:
        _logger = TradingLogger(name, log_file, log_level)
    return _logger


def setup_logger(
    name: str = "trading_system",
    log_file: Optional[Path] = None,
    log_level: str = "INFO",
    console_output: bool = True,
) -> TradingLogger:
    """Setup and return a new logger instance."""
    global _logger
    _logger = TradingLogger(name, log_file, log_level, console_output)
    return _logger
