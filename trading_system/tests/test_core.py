"""Basic unit tests for core components."""
import pytest
import asyncio
from pathlib import Path


class TestConfigLoader:
    """Test configuration loader."""
    
    def test_load_config(self):
        """Test loading configuration."""
        from trading_system.utils.config_loader import get_config_loader
        
        config_loader = get_config_loader()
        config = config_loader.load('config')
        
        assert config is not None
        assert 'system' in config
        assert 'trading' in config


class TestLogger:
    """Test logging system."""
    
    def test_logger_creation(self):
        """Test logger creation."""
        from trading_system.utils.logger import get_logger
        
        logger = get_logger()
        assert logger is not None
        
        logger.info("Test log message")


class TestMonitoring:
    """Test monitoring system."""
    
    def test_performance_monitor(self):
        """Test performance monitor."""
        from trading_system.utils.monitoring import get_monitor
        
        monitor = get_monitor()
        assert monitor is not None
        
        sys_metrics = monitor.get_system_metrics()
        assert sys_metrics.cpu_percent >= 0
        assert sys_metrics.memory_percent >= 0


@pytest.mark.asyncio
class TestDatabase:
    """Test database operations."""
    
    async def test_database_connection(self):
        """Test database connection."""
        from trading_system.utils.database import TradingDatabase
        
        db = TradingDatabase(Path("/tmp/test.db"))
        await db.connect()
        
        # Test inserting trade
        trade_data = {
            'symbol': 'XAUUSD',
            'action': 'buy',
            'volume': 0.01,
            'entry_price': 2000.0,
        }
        trade_id = await db.insert_trade(trade_data)
        assert trade_id > 0
        
        await db.close()


class TestMicrostructure:
    """Test microstructure features."""
    
    def test_vpin_calculator(self):
        """Test VPIN calculator."""
        from trading_system.features.microstructure import VPINCalculator
        
        vpin = VPINCalculator(bucket_size=10, window_size=10)
        
        # Add some ticks
        for i in range(20):
            price_change = 0.01 if i % 2 == 0 else -0.01
            vpin.add_tick(price_change, 1.0)
            
        vpin_value = vpin.calculate_vpin()
        assert 0 <= vpin_value <= 1.0


class TestTechnicalIndicators:
    """Test technical indicators."""
    
    def test_atr_calculation(self):
        """Test ATR calculation."""
        import numpy as np
        from trading_system.features.technical_indicators import TechnicalIndicators
        
        high = np.array([2000, 2010, 2005, 2015, 2012])
        low = np.array([1990, 2000, 1995, 2005, 2002])
        close = np.array([1995, 2005, 2000, 2010, 2007])
        
        atr = TechnicalIndicators.atr(high, low, close, period=3)
        assert len(atr) == len(close)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
