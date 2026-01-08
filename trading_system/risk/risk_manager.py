"""Real-time risk management engine."""
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from trading_system.core.position_manager import get_position_manager
from trading_system.core.mt5_connector import get_mt5_connector
from trading_system.utils.logger import get_logger
from trading_system.utils.config_loader import get_config_loader


class RiskMode(Enum):
    """Risk management modes."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class RiskLimits:
    """Risk limit parameters."""
    risk_per_trade_percent: float
    max_concurrent_positions: int
    max_daily_loss_percent: float
    max_drawdown_percent: float
    position_size_multiplier: float
    take_profit_atr_multiplier: float
    stop_loss_atr_multiplier: float
    trailing_stop_enabled: bool
    trailing_stop_atr_multiplier: float
    max_leverage: float


class RiskManager:
    """Real-time risk management system."""
    
    def __init__(self, risk_mode: RiskMode = RiskMode.MODERATE):
        """
        Initialize risk manager.
        
        Args:
            risk_mode: Risk management mode
        """
        self.risk_mode = risk_mode
        self.logger = get_logger()
        self.config_loader = get_config_loader()
        self.position_manager = get_position_manager()
        self.mt5_connector = get_mt5_connector()
        
        # Load risk parameters
        self.risk_limits = self._load_risk_limits()
        
        # State tracking
        self.daily_pnl = 0.0
        self.daily_start_equity = 0.0
        self.peak_equity = 0.0
        self.max_drawdown = 0.0
        self.trading_enabled = True
        
        # Performance tracking
        self._last_update_time = datetime.utcnow()
        
    def _load_risk_limits(self) -> RiskLimits:
        """Load risk limits from configuration."""
        risk_config = self.config_loader.load('risk_profiles')
        mode_config = risk_config[self.risk_mode.value]
        
        return RiskLimits(
            risk_per_trade_percent=mode_config['risk_per_trade_percent'],
            max_concurrent_positions=mode_config['max_concurrent_positions'],
            max_daily_loss_percent=mode_config['max_daily_loss_percent'],
            max_drawdown_percent=mode_config['max_drawdown_percent'],
            position_size_multiplier=mode_config['position_size_multiplier'],
            take_profit_atr_multiplier=mode_config['take_profit_atr_multiplier'],
            stop_loss_atr_multiplier=mode_config['stop_loss_atr_multiplier'],
            trailing_stop_enabled=mode_config['trailing_stop_enabled'],
            trailing_stop_atr_multiplier=mode_config['trailing_stop_atr_multiplier'],
            max_leverage=mode_config['max_leverage'],
        )
        
    async def update_risk_metrics(self) -> None:
        """Update risk metrics from account state."""
        account_info = self.mt5_connector.get_account_info()
        
        if account_info is None:
            return
            
        # Initialize daily tracking if needed
        current_date = datetime.utcnow().date()
        if not hasattr(self, '_last_date') or self._last_date != current_date:
            self.daily_start_equity = account_info.equity
            self.daily_pnl = 0.0
            self._last_date = current_date
            
        # Update daily P&L
        self.daily_pnl = account_info.equity - self.daily_start_equity
        
        # Update peak equity and drawdown
        if account_info.equity > self.peak_equity:
            self.peak_equity = account_info.equity
            
        current_drawdown = (self.peak_equity - account_info.equity) / self.peak_equity * 100
        self.max_drawdown = max(self.max_drawdown, current_drawdown)
        
        # Check risk limits
        await self._check_risk_limits(account_info)
        
    async def _check_risk_limits(self, account_info: Any) -> None:
        """Check if risk limits are breached."""
        # Check daily loss limit
        daily_loss_percent = (self.daily_pnl / self.daily_start_equity) * 100
        if daily_loss_percent < -self.risk_limits.max_daily_loss_percent:
            self.logger.critical(
                "Daily loss limit exceeded",
                daily_loss_percent=daily_loss_percent,
                limit=self.risk_limits.max_daily_loss_percent
            )
            await self.emergency_stop("Daily loss limit exceeded")
            
        # Check drawdown limit
        if self.max_drawdown > self.risk_limits.max_drawdown_percent:
            self.logger.critical(
                "Maximum drawdown exceeded",
                drawdown=self.max_drawdown,
                limit=self.risk_limits.max_drawdown_percent
            )
            await self.emergency_stop("Maximum drawdown exceeded")
            
    def can_open_position(self, symbol: str) -> Tuple[bool, str]:
        """
        Check if new position can be opened.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Tuple of (can_open, reason)
        """
        if not self.trading_enabled:
            return False, "Trading disabled"
            
        # Check position count
        current_positions = self.position_manager.get_position_count()
        if current_positions >= self.risk_limits.max_concurrent_positions:
            return False, f"Max positions reached ({current_positions}/{self.risk_limits.max_concurrent_positions})"
            
        # Check daily loss
        if self.daily_start_equity > 0:
            daily_loss_percent = (self.daily_pnl / self.daily_start_equity) * 100
            if daily_loss_percent < -self.risk_limits.max_daily_loss_percent:
                return False, "Daily loss limit reached"
                
        return True, "OK"
        
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        account_equity: float,
        atr: Optional[float] = None
    ) -> float:
        """
        Calculate position size based on risk parameters.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            account_equity: Current account equity
            atr: Average True Range (optional)
            
        Returns:
            Position size in lots
        """
        # Calculate risk amount
        risk_amount = account_equity * (self.risk_limits.risk_per_trade_percent / 100)
        
        # Calculate stop loss distance
        sl_distance = abs(entry_price - stop_loss)
        
        if sl_distance == 0:
            return 0.0
            
        # Get symbol info
        symbol_info = self.mt5_connector.get_symbol_info(symbol)
        if symbol_info is None:
            return 0.0
            
        contract_size = symbol_info['trade_contract_size']
        point = symbol_info['point']
        
        # Calculate position size
        # risk_amount = position_size * contract_size * (sl_distance / point)
        position_size = risk_amount / (contract_size * sl_distance)
        
        # Apply position size multiplier based on risk mode
        position_size *= self.risk_limits.position_size_multiplier
        
        # Apply volume constraints
        min_volume = symbol_info['volume_min']
        max_volume = symbol_info['volume_max']
        volume_step = symbol_info['volume_step']
        
        # Round to volume step
        position_size = round(position_size / volume_step) * volume_step
        
        # Clamp to min/max
        position_size = max(min_volume, min(position_size, max_volume))
        
        return position_size
        
    def calculate_stop_loss(
        self,
        entry_price: float,
        side: str,
        atr: float
    ) -> float:
        """
        Calculate stop loss price.
        
        Args:
            entry_price: Entry price
            side: 'long' or 'short'
            atr: Average True Range
            
        Returns:
            Stop loss price
        """
        sl_distance = atr * self.risk_limits.stop_loss_atr_multiplier
        
        if side == 'long':
            return entry_price - sl_distance
        else:
            return entry_price + sl_distance
            
    def calculate_take_profit(
        self,
        entry_price: float,
        side: str,
        atr: float
    ) -> float:
        """
        Calculate take profit price.
        
        Args:
            entry_price: Entry price
            side: 'long' or 'short'
            atr: Average True Range
            
        Returns:
            Take profit price
        """
        tp_distance = atr * self.risk_limits.take_profit_atr_multiplier
        
        if side == 'long':
            return entry_price + tp_distance
        else:
            return entry_price - tp_distance
            
    async def emergency_stop(self, reason: str) -> None:
        """
        Emergency stop - close all positions and disable trading.
        
        Args:
            reason: Reason for emergency stop
        """
        self.logger.critical("EMERGENCY STOP TRIGGERED", reason=reason)
        
        # Disable trading
        self.trading_enabled = False
        
        # Close all positions
        try:
            count = await self.position_manager.close_all_positions()
            self.logger.info(f"Closed {count} positions during emergency stop")
        except Exception as e:
            self.logger.error("Failed to close positions during emergency", error=str(e))
            
    def enable_trading(self) -> None:
        """Re-enable trading."""
        self.trading_enabled = True
        self.logger.info("Trading enabled")
        
    def disable_trading(self) -> None:
        """Disable trading."""
        self.trading_enabled = False
        self.logger.info("Trading disabled")
        
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get risk management summary."""
        account_info = self.mt5_connector.get_account_info()
        
        summary = {
            'risk_mode': self.risk_mode.value,
            'trading_enabled': self.trading_enabled,
            'daily_pnl': self.daily_pnl,
            'daily_pnl_percent': (self.daily_pnl / self.daily_start_equity * 100) if self.daily_start_equity > 0 else 0,
            'max_drawdown': self.max_drawdown,
            'current_positions': self.position_manager.get_position_count(),
            'max_positions': self.risk_limits.max_concurrent_positions,
        }
        
        if account_info:
            summary.update({
                'equity': account_info.equity,
                'balance': account_info.balance,
                'margin_level': account_info.margin_level,
            })
            
        return summary


# Global risk manager instance
_risk_manager: Optional[RiskManager] = None


def get_risk_manager(risk_mode: RiskMode = RiskMode.MODERATE) -> RiskManager:
    """Get the global risk manager instance."""
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = RiskManager(risk_mode)
    return _risk_manager
