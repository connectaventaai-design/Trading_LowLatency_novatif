"""MetaTrader 5 API wrapper with connection pooling."""
import MetaTrader5 as mt5
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum

from trading_system.utils.logger import get_logger
from trading_system.utils.config_loader import get_config_loader


class OrderType(Enum):
    """Order types."""
    BUY = mt5.ORDER_TYPE_BUY
    SELL = mt5.ORDER_TYPE_SELL
    BUY_LIMIT = mt5.ORDER_TYPE_BUY_LIMIT
    SELL_LIMIT = mt5.ORDER_TYPE_SELL_LIMIT
    BUY_STOP = mt5.ORDER_TYPE_BUY_STOP
    SELL_STOP = mt5.ORDER_TYPE_SELL_STOP


@dataclass
class TickData:
    """Tick data structure."""
    timestamp: float
    bid: float
    ask: float
    last: float
    volume: int
    time_msc: int
    flags: int
    volume_real: float


@dataclass
class AccountInfo:
    """Account information structure."""
    login: int
    balance: float
    equity: float
    profit: float
    margin: float
    margin_free: float
    margin_level: float
    leverage: int
    currency: str


class MT5Connector:
    """MetaTrader 5 API wrapper with advanced features."""
    
    def __init__(self):
        """Initialize MT5 connector."""
        self.logger = get_logger()
        self.config_loader = get_config_loader()
        self.connected = False
        self._connection_lock = asyncio.Lock()
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        
    async def connect(self) -> bool:
        """
        Connect to MT5 terminal.
        
        Returns:
            True if connected successfully
        """
        async with self._connection_lock:
            if self.connected:
                return True
                
            try:
                # Load MT5 configuration
                mt5_config = self.config_loader.load('mt5_config')
                account_config = mt5_config['account']
                
                # Initialize MT5
                if not mt5.initialize():
                    self.logger.error("Failed to initialize MT5", error=mt5.last_error())
                    return False
                    
                # Get connection details from environment
                account = int(self.config_loader.get_env('MT5_ACCOUNT', '0'))
                password = self.config_loader.get_env('MT5_PASSWORD', '')
                server = self.config_loader.get_env('MT5_SERVER', '')
                
                # Login to account
                if account and password and server:
                    if not mt5.login(account, password=password, server=server):
                        self.logger.error("Failed to login to MT5", error=mt5.last_error())
                        mt5.shutdown()
                        return False
                        
                self.connected = True
                self._reconnect_attempts = 0
                
                account_info = self.get_account_info()
                self.logger.info(
                    "Connected to MT5",
                    account=account_info.login if account_info else None,
                    balance=account_info.balance if account_info else None
                )
                
                return True
                
            except Exception as e:
                self.logger.error("Exception during MT5 connection", error=str(e))
                return False
                
    async def disconnect(self) -> None:
        """Disconnect from MT5 terminal."""
        async with self._connection_lock:
            if self.connected:
                mt5.shutdown()
                self.connected = False
                self.logger.info("Disconnected from MT5")
                
    async def ensure_connected(self) -> bool:
        """
        Ensure connection to MT5 is active.
        
        Returns:
            True if connected
        """
        if not self.connected:
            return await self.connect()
            
        # Check if connection is still alive
        if mt5.terminal_info() is None:
            self.logger.warning("MT5 connection lost, attempting reconnect")
            self.connected = False
            return await self._reconnect()
            
        return True
        
    async def _reconnect(self) -> bool:
        """
        Attempt to reconnect to MT5.
        
        Returns:
            True if reconnected successfully
        """
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            self.logger.error("Max reconnection attempts reached")
            return False
            
        self._reconnect_attempts += 1
        wait_time = min(2 ** self._reconnect_attempts, 60)  # Exponential backoff
        
        self.logger.info(f"Reconnecting to MT5 (attempt {self._reconnect_attempts})")
        await asyncio.sleep(wait_time)
        
        return await self.connect()
        
    def get_account_info(self) -> Optional[AccountInfo]:
        """
        Get account information.
        
        Returns:
            AccountInfo object or None
        """
        if not self.connected:
            return None
            
        account_info = mt5.account_info()
        if account_info is None:
            return None
            
        return AccountInfo(
            login=account_info.login,
            balance=account_info.balance,
            equity=account_info.equity,
            profit=account_info.profit,
            margin=account_info.margin,
            margin_free=account_info.margin_free,
            margin_level=account_info.margin_level,
            leverage=account_info.leverage,
            currency=account_info.currency,
        )
        
    async def get_tick(self, symbol: str) -> Optional[TickData]:
        """
        Get latest tick for symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            TickData object or None
        """
        if not await self.ensure_connected():
            return None
            
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
            
        return TickData(
            timestamp=tick.time,
            bid=tick.bid,
            ask=tick.ask,
            last=tick.last,
            volume=tick.volume,
            time_msc=tick.time_msc,
            flags=tick.flags,
            volume_real=tick.volume_real,
        )
        
    async def get_ticks(
        self,
        symbol: str,
        count: int = 1000,
        from_timestamp: Optional[datetime] = None
    ) -> Optional[List[TickData]]:
        """
        Get historical ticks.
        
        Args:
            symbol: Trading symbol
            count: Number of ticks to retrieve
            from_timestamp: Start timestamp
            
        Returns:
            List of TickData objects or None
        """
        if not await self.ensure_connected():
            return None
            
        if from_timestamp is None:
            from_timestamp = datetime.now() - timedelta(hours=1)
            
        ticks = mt5.copy_ticks_from(symbol, from_timestamp, count, mt5.COPY_TICKS_ALL)
        
        if ticks is None or len(ticks) == 0:
            return None
            
        return [
            TickData(
                timestamp=tick['time'],
                bid=tick['bid'],
                ask=tick['ask'],
                last=tick['last'],
                volume=tick['volume'],
                time_msc=tick['time_msc'],
                flags=tick['flags'],
                volume_real=tick['volume_real'],
            )
            for tick in ticks
        ]
        
    async def get_bars(
        self,
        symbol: str,
        timeframe: int = mt5.TIMEFRAME_M1,
        count: int = 1000,
        from_timestamp: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Get historical bars.
        
        Args:
            symbol: Trading symbol
            timeframe: MT5 timeframe constant
            count: Number of bars
            from_timestamp: Start timestamp
            
        Returns:
            DataFrame with OHLCV data or None
        """
        if not await self.ensure_connected():
            return None
            
        if from_timestamp:
            rates = mt5.copy_rates_from(symbol, timeframe, from_timestamp, count)
        else:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            
        if rates is None or len(rates) == 0:
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
        
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol information.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with symbol info or None
        """
        if not self.connected:
            return None
            
        info = mt5.symbol_info(symbol)
        if info is None:
            return None
            
        return {
            'name': info.name,
            'point': info.point,
            'digits': info.digits,
            'spread': info.spread,
            'trade_contract_size': info.trade_contract_size,
            'volume_min': info.volume_min,
            'volume_max': info.volume_max,
            'volume_step': info.volume_step,
            'trade_tick_size': info.trade_tick_size,
            'trade_tick_value': info.trade_tick_value,
        }
        
    async def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get open positions.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of position dictionaries
        """
        if not await self.ensure_connected():
            return []
            
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
            
        if positions is None:
            return []
            
        return [
            {
                'ticket': pos.ticket,
                'time': pos.time,
                'symbol': pos.symbol,
                'type': pos.type,
                'volume': pos.volume,
                'price_open': pos.price_open,
                'price_current': pos.price_current,
                'sl': pos.sl,
                'tp': pos.tp,
                'profit': pos.profit,
                'magic': pos.magic,
                'comment': pos.comment,
            }
            for pos in positions
        ]
        
    def check_connection(self) -> bool:
        """
        Check if MT5 is connected.
        
        Returns:
            True if connected
        """
        if not self.connected:
            return False
            
        terminal_info = mt5.terminal_info()
        return terminal_info is not None and terminal_info.connected


# Global connector instance
_connector: Optional[MT5Connector] = None


def get_mt5_connector() -> MT5Connector:
    """Get the global MT5 connector instance."""
    global _connector
    if _connector is None:
        _connector = MT5Connector()
    return _connector
