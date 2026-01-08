"""Real-time tick data processing with buffers."""
import asyncio
import numpy as np
from collections import deque
from typing import Deque, Optional, List, Dict, Any
from dataclasses import dataclass
import time

from trading_system.core.mt5_connector import get_mt5_connector, TickData
from trading_system.utils.logger import get_logger


@dataclass
class TickBuffer:
    """Tick buffer with statistical calculations."""
    timestamps: Deque[float]
    bids: Deque[float]
    asks: Deque[float]
    spreads: Deque[float]
    mid_prices: Deque[float]
    volumes: Deque[int]
    max_size: int
    
    def __init__(self, max_size: int = 10000):
        """Initialize tick buffer."""
        self.max_size = max_size
        self.timestamps = deque(maxlen=max_size)
        self.bids = deque(maxlen=max_size)
        self.asks = deque(maxlen=max_size)
        self.spreads = deque(maxlen=max_size)
        self.mid_prices = deque(maxlen=max_size)
        self.volumes = deque(maxlen=max_size)
        
    def add_tick(self, tick: TickData) -> None:
        """Add tick to buffer."""
        self.timestamps.append(tick.timestamp)
        self.bids.append(tick.bid)
        self.asks.append(tick.ask)
        spread = tick.ask - tick.bid
        self.spreads.append(spread)
        mid_price = (tick.bid + tick.ask) / 2
        self.mid_prices.append(mid_price)
        self.volumes.append(tick.volume)
        
    def get_recent_ticks(self, n: int) -> Dict[str, np.ndarray]:
        """
        Get recent n ticks as numpy arrays.
        
        Args:
            n: Number of recent ticks
            
        Returns:
            Dictionary with tick data arrays
        """
        n = min(n, len(self.timestamps))
        return {
            'timestamps': np.array(list(self.timestamps)[-n:]),
            'bids': np.array(list(self.bids)[-n:]),
            'asks': np.array(list(self.asks)[-n:]),
            'spreads': np.array(list(self.spreads)[-n:]),
            'mid_prices': np.array(list(self.mid_prices)[-n:]),
            'volumes': np.array(list(self.volumes)[-n:]),
        }
        
    @property
    def size(self) -> int:
        """Get current buffer size."""
        return len(self.timestamps)
        
    @property
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return self.size == 0
        
    def get_latest_tick(self) -> Optional[Dict[str, Any]]:
        """Get the latest tick."""
        if self.is_empty:
            return None
        return {
            'timestamp': self.timestamps[-1],
            'bid': self.bids[-1],
            'ask': self.asks[-1],
            'spread': self.spreads[-1],
            'mid_price': self.mid_prices[-1],
            'volume': self.volumes[-1],
        }
        
    def get_spread_stats(self) -> Dict[str, float]:
        """Get spread statistics."""
        if self.is_empty:
            return {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}
            
        spreads = np.array(list(self.spreads))
        return {
            'mean': float(np.mean(spreads)),
            'std': float(np.std(spreads)),
            'min': float(np.min(spreads)),
            'max': float(np.max(spreads)),
        }


class TickProcessor:
    """Real-time tick data processor with memory-mapped buffers."""
    
    def __init__(self, symbol: str, buffer_size: int = 10000):
        """
        Initialize tick processor.
        
        Args:
            symbol: Trading symbol
            buffer_size: Maximum buffer size
        """
        self.symbol = symbol
        self.buffer_size = buffer_size
        self.connector = get_mt5_connector()
        self.logger = get_logger()
        
        # Tick buffer
        self.buffer = TickBuffer(buffer_size)
        
        # Processing state
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        self._last_tick_time = 0.0
        
        # Callbacks for tick events
        self._tick_callbacks: List[callable] = []
        
    async def start(self, update_interval_ms: int = 100) -> None:
        """
        Start tick processing.
        
        Args:
            update_interval_ms: Update interval in milliseconds
        """
        if self._running:
            return
            
        self._running = True
        self._update_task = asyncio.create_task(
            self._update_loop(update_interval_ms / 1000.0)
        )
        self.logger.info(f"Tick processor started for {self.symbol}")
        
    async def stop(self) -> None:
        """Stop tick processing."""
        if not self._running:
            return
            
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
                
        self.logger.info(f"Tick processor stopped for {self.symbol}")
        
    async def _update_loop(self, interval: float) -> None:
        """Main update loop."""
        while self._running:
            try:
                # Get latest tick
                tick = await self.connector.get_tick(self.symbol)
                
                if tick and tick.timestamp != self._last_tick_time:
                    self._last_tick_time = tick.timestamp
                    
                    # Add to buffer
                    self.buffer.add_tick(tick)
                    
                    # Notify callbacks
                    for callback in self._tick_callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(tick)
                            else:
                                callback(tick)
                        except Exception as e:
                            self.logger.error(
                                "Error in tick callback",
                                error=str(e)
                            )
                            
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    "Error in tick update loop",
                    symbol=self.symbol,
                    error=str(e)
                )
                await asyncio.sleep(interval)
                
    def register_callback(self, callback: callable) -> None:
        """
        Register a callback for tick events.
        
        Args:
            callback: Function to call on each tick
        """
        self._tick_callbacks.append(callback)
        
    def unregister_callback(self, callback: callable) -> None:
        """
        Unregister a tick callback.
        
        Args:
            callback: Function to remove
        """
        if callback in self._tick_callbacks:
            self._tick_callbacks.remove(callback)
            
    def get_latest_tick(self) -> Optional[Dict[str, Any]]:
        """Get the latest tick from buffer."""
        return self.buffer.get_latest_tick()
        
    def get_recent_ticks(self, n: int = 100) -> Dict[str, np.ndarray]:
        """
        Get recent ticks.
        
        Args:
            n: Number of ticks to retrieve
            
        Returns:
            Dictionary with tick data arrays
        """
        return self.buffer.get_recent_ticks(n)
        
    def get_spread_stats(self) -> Dict[str, float]:
        """Get spread statistics."""
        return self.buffer.get_spread_stats()
        
    def get_tick_rate(self, window_seconds: int = 60) -> float:
        """
        Calculate tick arrival rate.
        
        Args:
            window_seconds: Time window for calculation
            
        Returns:
            Ticks per second
        """
        if self.buffer.is_empty:
            return 0.0
            
        timestamps = np.array(list(self.buffer.timestamps))
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        recent_ticks = timestamps[timestamps >= cutoff_time]
        
        if len(recent_ticks) < 2:
            return 0.0
            
        return len(recent_ticks) / window_seconds
        
    @property
    def buffer_utilization(self) -> float:
        """Get buffer utilization percentage."""
        return (self.buffer.size / self.buffer_size) * 100


# Global tick processors
_tick_processors: Dict[str, TickProcessor] = {}


def get_tick_processor(symbol: str, buffer_size: int = 10000) -> TickProcessor:
    """
    Get or create a tick processor for a symbol.
    
    Args:
        symbol: Trading symbol
        buffer_size: Buffer size
        
    Returns:
        TickProcessor instance
    """
    if symbol not in _tick_processors:
        _tick_processors[symbol] = TickProcessor(symbol, buffer_size)
    return _tick_processors[symbol]
