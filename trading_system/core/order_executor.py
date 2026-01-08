"""Async order execution engine."""
import MetaTrader5 as mt5
import asyncio
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from trading_system.core.mt5_connector import get_mt5_connector, OrderType
from trading_system.utils.logger import get_logger
from trading_system.utils.monitoring import get_monitor, LatencyTracker


class OrderResult(Enum):
    """Order execution result."""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    REJECTED = "rejected"


@dataclass
class ExecutionResult:
    """Order execution result data."""
    result: OrderResult
    ticket: Optional[int]
    volume: float
    price: float
    execution_time_ms: float
    slippage: float
    comment: str
    error_code: Optional[int] = None
    error_description: Optional[str] = None


class OrderExecutor:
    """High-performance async order executor."""
    
    def __init__(self, magic_number: int = 123456):
        """
        Initialize order executor.
        
        Args:
            magic_number: Magic number for orders
        """
        self.magic_number = magic_number
        self.connector = get_mt5_connector()
        self.logger = get_logger()
        self.monitor = get_monitor()
        self._execution_lock = asyncio.Lock()
        
    async def execute_market_order(
        self,
        symbol: str,
        order_type: OrderType,
        volume: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        comment: str = "",
        deviation: int = 10
    ) -> ExecutionResult:
        """
        Execute a market order.
        
        Args:
            symbol: Trading symbol
            order_type: Buy or Sell
            volume: Order volume
            stop_loss: Stop loss price
            take_profit: Take profit price
            comment: Order comment
            deviation: Max price deviation in points
            
        Returns:
            ExecutionResult object
        """
        start_time = time.perf_counter()
        
        try:
            # Ensure MT5 connection
            if not await self.connector.ensure_connected():
                return ExecutionResult(
                    result=OrderResult.FAILED,
                    ticket=None,
                    volume=volume,
                    price=0.0,
                    execution_time_ms=0.0,
                    slippage=0.0,
                    comment="MT5 not connected",
                )
                
            # Get current price
            tick = await self.connector.get_tick(symbol)
            if tick is None:
                return ExecutionResult(
                    result=OrderResult.FAILED,
                    ticket=None,
                    volume=volume,
                    price=0.0,
                    execution_time_ms=0.0,
                    slippage=0.0,
                    comment="Failed to get tick data",
                )
                
            # Determine price
            if order_type in [OrderType.BUY, OrderType.BUY_LIMIT, OrderType.BUY_STOP]:
                price = tick.ask
            else:
                price = tick.bid
                
            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type.value,
                "price": price,
                "deviation": deviation,
                "magic": self.magic_number,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            if stop_loss:
                request["sl"] = stop_loss
            if take_profit:
                request["tp"] = take_profit
                
            # Execute order
            async with self._execution_lock:
                result = mt5.order_send(request)
                
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            self.monitor.record_latency(execution_time_ms)
            
            if result is None:
                last_error = mt5.last_error()
                self.logger.error(
                    "Order execution failed",
                    symbol=symbol,
                    order_type=order_type.name,
                    volume=volume,
                    error=last_error
                )
                return ExecutionResult(
                    result=OrderResult.FAILED,
                    ticket=None,
                    volume=volume,
                    price=price,
                    execution_time_ms=execution_time_ms,
                    slippage=0.0,
                    comment="Order send failed",
                    error_code=last_error[0] if last_error else None,
                    error_description=last_error[1] if last_error else None,
                )
                
            # Check result
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.warning(
                    "Order rejected",
                    symbol=symbol,
                    retcode=result.retcode,
                    comment=result.comment
                )
                return ExecutionResult(
                    result=OrderResult.REJECTED,
                    ticket=result.order,
                    volume=volume,
                    price=result.price,
                    execution_time_ms=execution_time_ms,
                    slippage=abs(result.price - price),
                    comment=result.comment,
                    error_code=result.retcode,
                )
                
            # Success
            slippage = abs(result.price - price)
            self.logger.info(
                "Order executed",
                symbol=symbol,
                order_type=order_type.name,
                volume=volume,
                price=result.price,
                ticket=result.order,
                execution_time_ms=execution_time_ms,
                slippage=slippage
            )
            
            return ExecutionResult(
                result=OrderResult.SUCCESS,
                ticket=result.order,
                volume=result.volume,
                price=result.price,
                execution_time_ms=execution_time_ms,
                slippage=slippage,
                comment=result.comment,
            )
            
        except Exception as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error(
                "Exception during order execution",
                symbol=symbol,
                error=str(e),
                execution_time_ms=execution_time_ms
            )
            return ExecutionResult(
                result=OrderResult.FAILED,
                ticket=None,
                volume=volume,
                price=0.0,
                execution_time_ms=execution_time_ms,
                slippage=0.0,
                comment=f"Exception: {str(e)}",
            )
            
    async def close_position(
        self,
        ticket: int,
        volume: Optional[float] = None,
        deviation: int = 10
    ) -> ExecutionResult:
        """
        Close an open position.
        
        Args:
            ticket: Position ticket
            volume: Volume to close (None = close all)
            deviation: Max price deviation in points
            
        Returns:
            ExecutionResult object
        """
        start_time = time.perf_counter()
        
        try:
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return ExecutionResult(
                    result=OrderResult.FAILED,
                    ticket=None,
                    volume=0.0,
                    price=0.0,
                    execution_time_ms=0.0,
                    slippage=0.0,
                    comment="Position not found",
                )
                
            position = position[0]
            symbol = position.symbol
            pos_volume = volume if volume else position.volume
            
            # Determine close order type
            if position.type == mt5.ORDER_TYPE_BUY:
                close_type = mt5.ORDER_TYPE_SELL
            else:
                close_type = mt5.ORDER_TYPE_BUY
                
            # Get current price
            tick = await self.connector.get_tick(symbol)
            if tick is None:
                return ExecutionResult(
                    result=OrderResult.FAILED,
                    ticket=None,
                    volume=pos_volume,
                    price=0.0,
                    execution_time_ms=0.0,
                    slippage=0.0,
                    comment="Failed to get tick data",
                )
                
            price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
            
            # Prepare close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": pos_volume,
                "type": close_type,
                "position": ticket,
                "price": price,
                "deviation": deviation,
                "magic": self.magic_number,
                "comment": "Close position",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Execute close
            async with self._execution_lock:
                result = mt5.order_send(request)
                
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            self.monitor.record_latency(execution_time_ms)
            
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(
                    "Failed to close position",
                    ticket=ticket,
                    retcode=result.retcode if result else None,
                    comment=result.comment if result else "No result"
                )
                return ExecutionResult(
                    result=OrderResult.FAILED,
                    ticket=ticket,
                    volume=pos_volume,
                    price=price,
                    execution_time_ms=execution_time_ms,
                    slippage=0.0,
                    comment=result.comment if result else "Failed",
                    error_code=result.retcode if result else None,
                )
                
            self.logger.info(
                "Position closed",
                ticket=ticket,
                volume=result.volume,
                price=result.price,
                execution_time_ms=execution_time_ms
            )
            
            return ExecutionResult(
                result=OrderResult.SUCCESS,
                ticket=ticket,
                volume=result.volume,
                price=result.price,
                execution_time_ms=execution_time_ms,
                slippage=abs(result.price - price),
                comment="Position closed",
            )
            
        except Exception as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error(
                "Exception during position close",
                ticket=ticket,
                error=str(e)
            )
            return ExecutionResult(
                result=OrderResult.FAILED,
                ticket=ticket,
                volume=0.0,
                price=0.0,
                execution_time_ms=execution_time_ms,
                slippage=0.0,
                comment=f"Exception: {str(e)}",
            )
            
    async def close_all_positions(self, symbol: Optional[str] = None) -> int:
        """
        Close all open positions.
        
        Args:
            symbol: Filter by symbol (None = close all)
            
        Returns:
            Number of positions closed
        """
        positions = await self.connector.get_positions(symbol)
        closed_count = 0
        
        for position in positions:
            result = await self.close_position(position['ticket'])
            if result.result == OrderResult.SUCCESS:
                closed_count += 1
                
        return closed_count


# Global executor instance
_executor: Optional[OrderExecutor] = None


def get_order_executor(magic_number: int = 123456) -> OrderExecutor:
    """Get the global order executor instance."""
    global _executor
    if _executor is None:
        _executor = OrderExecutor(magic_number)
    return _executor
