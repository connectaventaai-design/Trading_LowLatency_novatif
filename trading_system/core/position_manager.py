"""Position tracking and management."""
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from trading_system.core.mt5_connector import get_mt5_connector
from trading_system.core.order_executor import get_order_executor
from trading_system.utils.logger import get_logger


class PositionSide(Enum):
    """Position side."""
    LONG = "long"
    SHORT = "short"


@dataclass
class Position:
    """Position data structure."""
    ticket: int
    symbol: str
    side: PositionSide
    volume: float
    entry_price: float
    current_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    profit: float
    entry_time: float
    magic: int
    comment: str
    
    @property
    def duration_seconds(self) -> float:
        """Get position duration in seconds."""
        return datetime.utcnow().timestamp() - self.entry_time
        
    @property
    def is_profitable(self) -> bool:
        """Check if position is profitable."""
        return self.profit > 0


class PositionManager:
    """Manage open positions and track P&L."""
    
    def __init__(self):
        """Initialize position manager."""
        self.connector = get_mt5_connector()
        self.executor = get_order_executor()
        self.logger = get_logger()
        self._positions: Dict[int, Position] = {}
        self._update_lock = asyncio.Lock()
        
    async def update_positions(self) -> None:
        """Update positions from MT5."""
        async with self._update_lock:
            try:
                # Get current positions from MT5
                mt5_positions = await self.connector.get_positions()
                
                # Update internal position tracking
                current_tickets = set()
                
                for mt5_pos in mt5_positions:
                    ticket = mt5_pos['ticket']
                    current_tickets.add(ticket)
                    
                    # Determine side
                    import MetaTrader5 as mt5
                    side = PositionSide.LONG if mt5_pos['type'] == mt5.ORDER_TYPE_BUY else PositionSide.SHORT
                    
                    # Create or update position
                    position = Position(
                        ticket=ticket,
                        symbol=mt5_pos['symbol'],
                        side=side,
                        volume=mt5_pos['volume'],
                        entry_price=mt5_pos['price_open'],
                        current_price=mt5_pos['price_current'],
                        stop_loss=mt5_pos.get('sl'),
                        take_profit=mt5_pos.get('tp'),
                        profit=mt5_pos['profit'],
                        entry_time=mt5_pos['time'],
                        magic=mt5_pos['magic'],
                        comment=mt5_pos.get('comment', ''),
                    )
                    
                    self._positions[ticket] = position
                    
                # Remove closed positions
                closed_tickets = set(self._positions.keys()) - current_tickets
                for ticket in closed_tickets:
                    self.logger.info(
                        "Position closed",
                        ticket=ticket,
                        profit=self._positions[ticket].profit
                    )
                    del self._positions[ticket]
                    
            except Exception as e:
                self.logger.error("Failed to update positions", error=str(e))
                
    def get_position(self, ticket: int) -> Optional[Position]:
        """
        Get position by ticket.
        
        Args:
            ticket: Position ticket
            
        Returns:
            Position object or None
        """
        return self._positions.get(ticket)
        
    def get_all_positions(self) -> List[Position]:
        """
        Get all open positions.
        
        Returns:
            List of Position objects
        """
        return list(self._positions.values())
        
    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """
        Get positions for a specific symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            List of Position objects
        """
        return [pos for pos in self._positions.values() if pos.symbol == symbol]
        
    def get_total_profit(self) -> float:
        """
        Get total profit across all positions.
        
        Returns:
            Total profit
        """
        return sum(pos.profit for pos in self._positions.values())
        
    def get_position_count(self, symbol: Optional[str] = None) -> int:
        """
        Get count of open positions.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            Position count
        """
        if symbol:
            return len(self.get_positions_by_symbol(symbol))
        return len(self._positions)
        
    def get_total_volume(self, symbol: Optional[str] = None) -> float:
        """
        Get total volume of open positions.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            Total volume
        """
        if symbol:
            positions = self.get_positions_by_symbol(symbol)
        else:
            positions = self.get_all_positions()
            
        return sum(pos.volume for pos in positions)
        
    def get_net_exposure(self, symbol: str) -> float:
        """
        Get net exposure for a symbol (long - short).
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Net exposure (positive = net long, negative = net short)
        """
        positions = self.get_positions_by_symbol(symbol)
        long_volume = sum(pos.volume for pos in positions if pos.side == PositionSide.LONG)
        short_volume = sum(pos.volume for pos in positions if pos.side == PositionSide.SHORT)
        return long_volume - short_volume
        
    async def close_position(self, ticket: int) -> bool:
        """
        Close a position.
        
        Args:
            ticket: Position ticket
            
        Returns:
            True if closed successfully
        """
        result = await self.executor.close_position(ticket)
        if result.result.value == "success":
            await self.update_positions()
            return True
        return False
        
    async def close_all_positions(self, symbol: Optional[str] = None) -> int:
        """
        Close all positions.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            Number of positions closed
        """
        count = await self.executor.close_all_positions(symbol)
        await self.update_positions()
        return count
        
    def get_position_summary(self) -> Dict[str, Any]:
        """
        Get summary of all positions.
        
        Returns:
            Dictionary with position summary
        """
        positions = self.get_all_positions()
        
        if not positions:
            return {
                'count': 0,
                'total_profit': 0.0,
                'total_volume': 0.0,
                'profitable_count': 0,
                'losing_count': 0,
            }
            
        return {
            'count': len(positions),
            'total_profit': sum(pos.profit for pos in positions),
            'total_volume': sum(pos.volume for pos in positions),
            'profitable_count': sum(1 for pos in positions if pos.is_profitable),
            'losing_count': sum(1 for pos in positions if not pos.is_profitable),
            'avg_profit': sum(pos.profit for pos in positions) / len(positions),
            'max_profit': max(pos.profit for pos in positions),
            'min_profit': min(pos.profit for pos in positions),
            'avg_duration_seconds': sum(pos.duration_seconds for pos in positions) / len(positions),
        }


# Global position manager instance
_position_manager: Optional[PositionManager] = None


def get_position_manager() -> PositionManager:
    """Get the global position manager instance."""
    global _position_manager
    if _position_manager is None:
        _position_manager = PositionManager()
    return _position_manager
