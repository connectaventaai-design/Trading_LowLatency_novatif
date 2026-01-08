"""Technical indicators optimized for GOLD trading."""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
import numba


@numba.jit(nopython=True, cache=True)
def calculate_atr_fast(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate ATR (Average True Range) - JIT compiled.
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ATR period
        
    Returns:
        ATR values
    """
    n = len(close)
    tr = np.zeros(n)
    atr = np.zeros(n)
    
    # Calculate True Range
    for i in range(1, n):
        h_l = high[i] - low[i]
        h_pc = abs(high[i] - close[i-1])
        l_pc = abs(low[i] - close[i-1])
        tr[i] = max(h_l, h_pc, l_pc)
        
    # Calculate ATR using Wilder's smoothing
    atr[period-1] = np.mean(tr[1:period])
    for i in range(period, n):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
        
    return atr


@numba.jit(nopython=True, cache=True)
def calculate_ema_fast(prices: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate EMA (Exponential Moving Average) - JIT compiled.
    
    Args:
        prices: Price array
        period: EMA period
        
    Returns:
        EMA values
    """
    n = len(prices)
    ema = np.zeros(n)
    multiplier = 2.0 / (period + 1)
    
    # Initial SMA
    ema[period-1] = np.mean(prices[:period])
    
    # Calculate EMA
    for i in range(period, n):
        ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]
        
    return ema


@numba.jit(nopython=True, cache=True)
def calculate_rsi_fast(prices: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate RSI (Relative Strength Index) - JIT compiled.
    
    Args:
        prices: Price array
        period: RSI period
        
    Returns:
        RSI values
    """
    n = len(prices)
    rsi = np.zeros(n)
    
    if n < period + 1:
        return rsi
        
    # Calculate price changes
    deltas = np.diff(prices)
    
    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # Initial averages
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    # Calculate RSI
    for i in range(period, n-1):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            rsi[i+1] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[i+1] = 100.0 - (100.0 / (1.0 + rs))
            
    return rsi


class TechnicalIndicators:
    """Technical indicators calculator for GOLD trading."""
    
    @staticmethod
    def atr(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """
        Calculate Average True Range.
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period
            
        Returns:
            ATR values
        """
        return calculate_atr_fast(high, low, close, period)
        
    @staticmethod
    def ema(prices: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate Exponential Moving Average.
        
        Args:
            prices: Price array
            period: EMA period
            
        Returns:
            EMA values
        """
        return calculate_ema_fast(prices, period)
        
    @staticmethod
    def rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Calculate Relative Strength Index.
        
        Args:
            prices: Price array
            period: RSI period
            
        Returns:
            RSI values
        """
        return calculate_rsi_fast(prices, period)
        
    @staticmethod
    def macd(
        prices: np.ndarray,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Price array
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            
        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        fast_ema = calculate_ema_fast(prices, fast_period)
        slow_ema = calculate_ema_fast(prices, slow_period)
        
        macd_line = fast_ema - slow_ema
        signal_line = calculate_ema_fast(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
        
    @staticmethod
    def bollinger_bands(
        prices: np.ndarray,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: Price array
            period: Period for moving average
            std_dev: Number of standard deviations
            
        Returns:
            Tuple of (Upper band, Middle band, Lower band)
        """
        n = len(prices)
        middle_band = np.zeros(n)
        upper_band = np.zeros(n)
        lower_band = np.zeros(n)
        
        for i in range(period-1, n):
            window = prices[i-period+1:i+1]
            middle = np.mean(window)
            std = np.std(window)
            
            middle_band[i] = middle
            upper_band[i] = middle + std_dev * std
            lower_band[i] = middle - std_dev * std
            
        return upper_band, middle_band, lower_band
        
    @staticmethod
    def adaptive_ma(
        prices: np.ndarray,
        volatility: np.ndarray,
        base_period: int = 20,
        min_period: int = 5,
        max_period: int = 50
    ) -> np.ndarray:
        """
        Calculate volatility-adjusted adaptive moving average.
        
        Args:
            prices: Price array
            volatility: Volatility array (e.g., ATR)
            base_period: Base period
            min_period: Minimum period
            max_period: Maximum period
            
        Returns:
            Adaptive MA values
        """
        n = len(prices)
        ama = np.zeros(n)
        
        # Normalize volatility
        vol_norm = volatility / np.max(volatility) if np.max(volatility) > 0 else volatility
        
        for i in range(max_period, n):
            # Adjust period based on volatility
            # High volatility -> shorter period (more reactive)
            # Low volatility -> longer period (more stable)
            period = int(base_period - (vol_norm[i] * (base_period - min_period)))
            period = max(min_period, min(period, max_period))
            
            ama[i] = np.mean(prices[i-period+1:i+1])
            
        return ama
        
    @staticmethod
    def volume_profile(
        prices: np.ndarray,
        volumes: np.ndarray,
        n_bins: int = 50
    ) -> Tuple[np.ndarray, float, float, float]:
        """
        Calculate volume profile.
        
        Args:
            prices: Price array
            volumes: Volume array
            n_bins: Number of price bins
            
        Returns:
            Tuple of (volume profile, POC, VAH, VAL)
            POC = Point of Control (price with highest volume)
            VAH = Value Area High
            VAL = Value Area Low
        """
        # Create price bins
        price_range = (np.min(prices), np.max(prices))
        bins = np.linspace(price_range[0], price_range[1], n_bins + 1)
        
        # Accumulate volume in each bin
        volume_profile = np.zeros(n_bins)
        for i in range(len(prices)):
            bin_idx = np.searchsorted(bins, prices[i]) - 1
            bin_idx = max(0, min(bin_idx, n_bins - 1))
            volume_profile[bin_idx] += volumes[i]
            
        # Find POC (Point of Control)
        poc_idx = np.argmax(volume_profile)
        poc_price = (bins[poc_idx] + bins[poc_idx + 1]) / 2
        
        # Calculate Value Area (70% of volume)
        total_volume = np.sum(volume_profile)
        value_area_volume = total_volume * 0.70
        
        # Expand from POC to find VAH and VAL
        current_volume = volume_profile[poc_idx]
        low_idx = poc_idx
        high_idx = poc_idx
        
        while current_volume < value_area_volume:
            # Expand to the side with more volume
            if low_idx > 0 and high_idx < n_bins - 1:
                if volume_profile[low_idx - 1] > volume_profile[high_idx + 1]:
                    low_idx -= 1
                    current_volume += volume_profile[low_idx]
                else:
                    high_idx += 1
                    current_volume += volume_profile[high_idx]
            elif low_idx > 0:
                low_idx -= 1
                current_volume += volume_profile[low_idx]
            elif high_idx < n_bins - 1:
                high_idx += 1
                current_volume += volume_profile[high_idx]
            else:
                break
                
        vah = (bins[high_idx] + bins[high_idx + 1]) / 2
        val = (bins[low_idx] + bins[low_idx + 1]) / 2
        
        return volume_profile, poc_price, vah, val
        
    @staticmethod
    def momentum(prices: np.ndarray, period: int = 10) -> np.ndarray:
        """
        Calculate price momentum.
        
        Args:
            prices: Price array
            period: Lookback period
            
        Returns:
            Momentum values
        """
        n = len(prices)
        momentum = np.zeros(n)
        
        for i in range(period, n):
            momentum[i] = prices[i] - prices[i - period]
            
        return momentum
        
    @staticmethod
    def zscore(prices: np.ndarray, window: int = 20) -> np.ndarray:
        """
        Calculate rolling z-score for regime detection.
        
        Args:
            prices: Price array
            window: Rolling window size
            
        Returns:
            Z-score values
        """
        n = len(prices)
        zscore = np.zeros(n)
        
        for i in range(window, n):
            window_data = prices[i-window+1:i+1]
            mean = np.mean(window_data)
            std = np.std(window_data)
            
            if std > 0:
                zscore[i] = (prices[i] - mean) / std
            else:
                zscore[i] = 0.0
                
        return zscore
