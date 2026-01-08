"""Advanced market microstructure analysis - VPIN, spread analysis, entropy, imbalance."""
import numpy as np
from typing import Dict, Any, Optional, Tuple
from collections import deque
from scipy import stats
import numba


@numba.jit(nopython=True, cache=True)
def calculate_entropy_fast(price_changes: np.ndarray) -> float:
    """
    Calculate entropy of price changes (JIT compiled).
    
    Args:
        price_changes: Array of price changes
        
    Returns:
        Shannon entropy
    """
    if len(price_changes) == 0:
        return 0.0
        
    # Bin the price changes
    hist, _ = np.histogram(price_changes, bins=20)
    
    # Calculate probability distribution
    probs = hist / np.sum(hist)
    
    # Calculate entropy
    entropy = 0.0
    for p in probs:
        if p > 0:
            entropy -= p * np.log2(p)
            
    return entropy


class VPINCalculator:
    """Volume-Synchronized Probability of Informed Trading (VPIN) calculator."""
    
    def __init__(self, bucket_size: int = 50, window_size: int = 50):
        """
        Initialize VPIN calculator.
        
        Args:
            bucket_size: Number of ticks per volume bucket
            window_size: Number of buckets for moving window
        """
        self.bucket_size = bucket_size
        self.window_size = window_size
        
        # Volume buckets
        self.buckets: deque = deque(maxlen=window_size)
        self.current_bucket = {'buy_volume': 0.0, 'sell_volume': 0.0}
        self.tick_count = 0
        
    def add_tick(self, price_change: float, volume: float) -> None:
        """
        Add tick to VPIN calculator.
        
        Args:
            price_change: Price change from previous tick
            volume: Tick volume
        """
        # Classify as buy or sell based on price change
        if price_change > 0:
            self.current_bucket['buy_volume'] += volume
        elif price_change < 0:
            self.current_bucket['sell_volume'] += volume
        else:
            # Split neutral ticks
            self.current_bucket['buy_volume'] += volume / 2
            self.current_bucket['sell_volume'] += volume / 2
            
        self.tick_count += 1
        
        # Complete bucket when reaching bucket_size
        if self.tick_count >= self.bucket_size:
            self.buckets.append(self.current_bucket.copy())
            self.current_bucket = {'buy_volume': 0.0, 'sell_volume': 0.0}
            self.tick_count = 0
            
    def calculate_vpin(self) -> float:
        """
        Calculate VPIN value.
        
        Returns:
            VPIN value between 0 and 1
        """
        if len(self.buckets) < 2:
            return 0.0
            
        total_imbalance = 0.0
        total_volume = 0.0
        
        for bucket in self.buckets:
            buy_vol = bucket['buy_volume']
            sell_vol = bucket['sell_volume']
            imbalance = abs(buy_vol - sell_vol)
            total_imbalance += imbalance
            total_volume += buy_vol + sell_vol
            
        if total_volume == 0:
            return 0.0
            
        vpin = total_imbalance / total_volume
        return min(vpin, 1.0)  # Cap at 1.0
        
    def is_toxic_flow(self, threshold: float = 0.7) -> bool:
        """
        Check if current flow is toxic.
        
        Args:
            threshold: VPIN threshold for toxicity
            
        Returns:
            True if flow is toxic
        """
        return self.calculate_vpin() > threshold


class SpreadRegimeClassifier:
    """Bid-ask spread regime classification."""
    
    def __init__(self, tight_threshold_pips: float = 2.0, wide_threshold_pips: float = 5.0):
        """
        Initialize spread classifier.
        
        Args:
            tight_threshold_pips: Threshold for tight spread in pips
            wide_threshold_pips: Threshold for wide spread in pips
        """
        self.tight_threshold = tight_threshold_pips * 0.01  # Convert to price
        self.wide_threshold = wide_threshold_pips * 0.01
        
        # Spread history
        self.spread_history: deque = deque(maxlen=1000)
        
    def add_spread(self, spread: float) -> None:
        """Add spread observation."""
        self.spread_history.append(spread)
        
    def classify_regime(self, current_spread: float) -> str:
        """
        Classify current spread regime.
        
        Args:
            current_spread: Current bid-ask spread
            
        Returns:
            Regime: 'tight', 'normal', or 'wide'
        """
        if current_spread < self.tight_threshold:
            return 'tight'
        elif current_spread > self.wide_threshold:
            return 'wide'
        else:
            return 'normal'
            
    def get_spread_stats(self) -> Dict[str, float]:
        """Get spread statistics."""
        if not self.spread_history:
            return {'mean': 0.0, 'std': 0.0, 'percentile_95': 0.0}
            
        spreads = np.array(self.spread_history)
        return {
            'mean': float(np.mean(spreads)),
            'std': float(np.std(spreads)),
            'median': float(np.median(spreads)),
            'percentile_95': float(np.percentile(spreads, 95)),
        }
        
    def is_compressed(self, current_spread: float, percentile: float = 25) -> bool:
        """
        Check if spread is compressed (favorable for entry).
        
        Args:
            current_spread: Current spread
            percentile: Percentile threshold
            
        Returns:
            True if spread is compressed
        """
        if len(self.spread_history) < 50:
            return False
            
        spreads = np.array(self.spread_history)
        threshold = np.percentile(spreads, percentile)
        return current_spread <= threshold


class TickDirectionEntropyAnalyzer:
    """Tick direction entropy analyzer for market uncertainty."""
    
    def __init__(self, window_size: int = 100):
        """
        Initialize entropy analyzer.
        
        Args:
            window_size: Window size for entropy calculation
        """
        self.window_size = window_size
        self.price_changes: deque = deque(maxlen=window_size)
        
    def add_price_change(self, price_change: float) -> None:
        """Add price change observation."""
        self.price_changes.append(price_change)
        
    def calculate_entropy(self) -> float:
        """
        Calculate entropy of tick directions.
        
        Returns:
            Shannon entropy (0 = deterministic, high = random)
        """
        if len(self.price_changes) < 10:
            return 0.0
            
        price_changes = np.array(self.price_changes)
        return calculate_entropy_fast(price_changes)
        
    def is_high_entropy(self, threshold: float = 0.8) -> bool:
        """
        Check if market is in high entropy (random) state.
        
        Args:
            threshold: Entropy threshold (normalized 0-1)
            
        Returns:
            True if entropy is high
        """
        entropy = self.calculate_entropy()
        max_entropy = np.log2(20)  # 20 bins in histogram
        normalized_entropy = entropy / max_entropy
        return normalized_entropy > threshold


class OrderBookImbalanceDetector:
    """Order book imbalance detector from tick data."""
    
    def __init__(self, window_size: int = 50):
        """
        Initialize imbalance detector.
        
        Args:
            window_size: Window size for imbalance calculation
        """
        self.window_size = window_size
        self.bid_volumes: deque = deque(maxlen=window_size)
        self.ask_volumes: deque = deque(maxlen=window_size)
        
    def add_tick(self, bid: float, ask: float, last_price: Optional[float] = None) -> None:
        """
        Add tick data for imbalance calculation.
        
        Args:
            bid: Bid price
            ask: Ask price
            last_price: Last trade price (optional)
        """
        # Infer volume from price proximity
        if last_price:
            if last_price >= ask:
                # Trade at ask - buying pressure
                self.ask_volumes.append(1.0)
                self.bid_volumes.append(0.0)
            elif last_price <= bid:
                # Trade at bid - selling pressure
                self.ask_volumes.append(0.0)
                self.bid_volumes.append(1.0)
            else:
                # Mid-market trade
                self.ask_volumes.append(0.5)
                self.bid_volumes.append(0.5)
        else:
            # No last price, assume balanced
            self.ask_volumes.append(0.5)
            self.bid_volumes.append(0.5)
            
    def calculate_imbalance(self) -> float:
        """
        Calculate order book imbalance.
        
        Returns:
            Imbalance ratio (-1 to 1, positive = buy pressure)
        """
        if not self.bid_volumes or not self.ask_volumes:
            return 0.0
            
        total_bid = sum(self.bid_volumes)
        total_ask = sum(self.ask_volumes)
        total = total_bid + total_ask
        
        if total == 0:
            return 0.0
            
        imbalance = (total_ask - total_bid) / total
        return imbalance
        
    def get_imbalance_strength(self) -> str:
        """
        Get imbalance strength classification.
        
        Returns:
            'strong_buy', 'weak_buy', 'balanced', 'weak_sell', 'strong_sell'
        """
        imbalance = self.calculate_imbalance()
        
        if imbalance > 0.6:
            return 'strong_buy'
        elif imbalance > 0.2:
            return 'weak_buy'
        elif imbalance < -0.6:
            return 'strong_sell'
        elif imbalance < -0.2:
            return 'weak_sell'
        else:
            return 'balanced'


class MicrostructureAnalyzer:
    """Combined microstructure analysis."""
    
    def __init__(
        self,
        vpin_bucket_size: int = 50,
        vpin_window_size: int = 50,
        spread_tight_threshold: float = 2.0,
        spread_wide_threshold: float = 5.0,
        entropy_window_size: int = 100,
        imbalance_window_size: int = 50,
    ):
        """Initialize microstructure analyzer."""
        self.vpin = VPINCalculator(vpin_bucket_size, vpin_window_size)
        self.spread_classifier = SpreadRegimeClassifier(
            spread_tight_threshold, spread_wide_threshold
        )
        self.entropy_analyzer = TickDirectionEntropyAnalyzer(entropy_window_size)
        self.imbalance_detector = OrderBookImbalanceDetector(imbalance_window_size)
        
        self.last_price = None
        
    def update(self, bid: float, ask: float, volume: float = 1.0) -> None:
        """
        Update all microstructure indicators.
        
        Args:
            bid: Bid price
            ask: Ask price
            volume: Tick volume
        """
        mid_price = (bid + ask) / 2
        spread = ask - bid
        
        # Update spread classifier
        self.spread_classifier.add_spread(spread)
        
        # Update VPIN
        if self.last_price is not None:
            price_change = mid_price - self.last_price
            self.vpin.add_tick(price_change, volume)
            self.entropy_analyzer.add_price_change(price_change)
            
        # Update imbalance detector
        self.imbalance_detector.add_tick(bid, ask, self.last_price)
        
        self.last_price = mid_price
        
    def get_analysis(self) -> Dict[str, Any]:
        """
        Get complete microstructure analysis.
        
        Returns:
            Dictionary with all microstructure metrics
        """
        return {
            'vpin': self.vpin.calculate_vpin(),
            'is_toxic_flow': self.vpin.is_toxic_flow(),
            'spread_regime': self.spread_classifier.classify_regime(
                self.spread_classifier.spread_history[-1] if self.spread_classifier.spread_history else 0.0
            ),
            'spread_stats': self.spread_classifier.get_spread_stats(),
            'entropy': self.entropy_analyzer.calculate_entropy(),
            'is_high_entropy': self.entropy_analyzer.is_high_entropy(),
            'order_imbalance': self.imbalance_detector.calculate_imbalance(),
            'imbalance_strength': self.imbalance_detector.get_imbalance_strength(),
        }
        
    def is_favorable_entry_condition(self) -> bool:
        """
        Check if microstructure conditions are favorable for entry.
        
        Returns:
            True if conditions are favorable
        """
        # Avoid toxic flow
        if self.vpin.is_toxic_flow():
            return False
            
        # Avoid high entropy (random) markets
        if self.entropy_analyzer.is_high_entropy():
            return False
            
        # Prefer compressed spreads
        if self.spread_classifier.spread_history:
            current_spread = self.spread_classifier.spread_history[-1]
            if not self.spread_classifier.is_compressed(current_spread):
                return False
                
        return True
