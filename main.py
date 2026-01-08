"""Main trading system loop."""
import asyncio
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional
import sys

from trading_system.core.mt5_connector import get_mt5_connector
from trading_system.core.position_manager import get_position_manager
from trading_system.core.tick_processor import get_tick_processor
from trading_system.core.order_executor import get_order_executor
from trading_system.risk.risk_manager import get_risk_manager, RiskMode
from trading_system.utils.logger import setup_logger, get_logger
from trading_system.utils.config_loader import get_config_loader
from trading_system.utils.database import TradingDatabase
from trading_system.utils.monitoring import get_monitor


class TradingSystem:
    """Main HFT trading system."""
    
    def __init__(self):
        """Initialize trading system."""
        # Load configuration
        self.config_loader = get_config_loader()
        self.config = self.config_loader.load('config')
        
        # Setup logger
        log_level = self.config_loader.get_env('LOG_LEVEL', 'INFO')
        log_file = Path(self.config_loader.get_env('LOG_FILE', 'logs/trading.log'))
        self.logger = setup_logger('trading_system', log_file, log_level)
        
        # Initialize components
        self.mt5_connector = get_mt5_connector()
        self.position_manager = get_position_manager()
        self.order_executor = get_order_executor(
            self.config['trading']['magic_number']
        )
        
        # Risk management
        risk_mode_str = self.config_loader.get_env('RISK_MODE', 'moderate')
        risk_mode = RiskMode(risk_mode_str)
        self.risk_manager = get_risk_manager(risk_mode)
        
        # Monitoring
        self.monitor = get_monitor()
        
        # Database
        db_path = Path(self.config_loader.get_env('DB_PATH', 'data/trading.db'))
        self.database = TradingDatabase(db_path)
        
        # Trading state
        self.running = False
        self.paper_trading = self.config_loader.get_env('PAPER_TRADING', 'true').lower() == 'true'
        
        # Symbol
        self.symbol = self.config['trading']['symbol']
        
        # Tick processor
        self.tick_processor = get_tick_processor(self.symbol)
        
        self.logger.info(
            "Trading system initialized",
            symbol=self.symbol,
            paper_trading=self.paper_trading,
            risk_mode=risk_mode.value
        )
        
    async def start(self) -> None:
        """Start the trading system."""
        self.logger.info("Starting HFT Trading System...")
        
        try:
            # Connect to MT5
            if not await self.mt5_connector.connect():
                self.logger.error("Failed to connect to MT5")
                return
                
            # Connect to database
            await self.database.connect()
            
            # Start tick processor
            await self.tick_processor.start(update_interval_ms=100)
            
            # Set running flag
            self.running = True
            
            # Start main loop
            await self._main_loop()
            
        except Exception as e:
            self.logger.error(f"Error starting trading system: {str(e)}")
            await self.shutdown()
            
    async def _main_loop(self) -> None:
        """Main trading loop."""
        self.logger.info("Entering main trading loop")
        
        last_risk_update = datetime.utcnow()
        last_position_update = datetime.utcnow()
        last_performance_log = datetime.utcnow()
        
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                # Update risk metrics (every second)
                if (current_time - last_risk_update).total_seconds() >= 1.0:
                    await self.risk_manager.update_risk_metrics()
                    last_risk_update = current_time
                    
                # Update positions (every 100ms)
                if (current_time - last_position_update).total_seconds() >= 0.1:
                    await self.position_manager.update_positions()
                    last_position_update = current_time
                    
                # Log performance (every 60 seconds)
                if (current_time - last_performance_log).total_seconds() >= 60.0:
                    await self._log_performance()
                    last_performance_log = current_time
                    
                # Trading logic would go here
                # This is where signals would be generated and trades executed
                # For now, just monitoring
                
                # Sleep briefly to avoid busy-waiting
                await asyncio.sleep(0.01)  # 10ms
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {str(e)}")
                await asyncio.sleep(1.0)
                
        self.logger.info("Exiting main trading loop")
        
    async def _log_performance(self) -> None:
        """Log performance metrics."""
        # System metrics
        sys_metrics = self.monitor.get_system_metrics()
        self.logger.info(
            "System metrics",
            cpu_percent=sys_metrics.cpu_percent,
            memory_percent=sys_metrics.memory_percent,
            memory_used_mb=sys_metrics.memory_used_mb
        )
        
        # Latency stats
        latency_stats = self.monitor.get_latency_stats()
        self.logger.info(
            "Latency stats",
            avg_ms=latency_stats['avg'],
            p95_ms=latency_stats['p95'],
            p99_ms=latency_stats['p99']
        )
        
        # Position summary
        pos_summary = self.position_manager.get_position_summary()
        self.logger.info(
            "Position summary",
            count=pos_summary['count'],
            total_profit=pos_summary['total_profit']
        )
        
        # Risk summary
        risk_summary = self.risk_manager.get_risk_summary()
        self.logger.info(
            "Risk summary",
            daily_pnl=risk_summary['daily_pnl'],
            max_drawdown=risk_summary['max_drawdown']
        )
        
        # Save to database
        account_info = self.mt5_connector.get_account_info()
        if account_info:
            await self.database.insert_performance({
                'equity': account_info.equity,
                'balance': account_info.balance,
                'margin_used': account_info.margin,
                'free_margin': account_info.margin_free,
                'pnl_daily': risk_summary['daily_pnl'],
                'open_positions': pos_summary['count'],
                'total_trades': 0,  # Would track this
                'win_rate': 0.0,  # Would calculate this
                'sharpe_ratio': None,
                'drawdown': risk_summary['max_drawdown'],
            })
            
    async def shutdown(self) -> None:
        """Graceful shutdown."""
        self.logger.info("Shutting down trading system...")
        
        self.running = False
        
        # Stop tick processor
        await self.tick_processor.stop()
        
        # Close all positions if configured
        if self.config['shutdown']['force_close_positions']:
            self.logger.info("Closing all positions...")
            await self.position_manager.close_all_positions()
            
        # Disconnect from MT5
        await self.mt5_connector.disconnect()
        
        # Close database
        await self.database.close()
        
        self.logger.info("Trading system shutdown complete")
        

async def main():
    """Main entry point."""
    trading_system = TradingSystem()
    
    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    
    def signal_handler(signum, frame):
        """Handle shutdown signals."""
        trading_system.logger.info(f"Received signal {signum}")
        loop.create_task(trading_system.shutdown())
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start trading system
    try:
        await trading_system.start()
    except KeyboardInterrupt:
        trading_system.logger.info("Keyboard interrupt received")
    finally:
        await trading_system.shutdown()


if __name__ == "__main__":
    # Use uvloop for better performance if available
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass
        
    asyncio.run(main())
