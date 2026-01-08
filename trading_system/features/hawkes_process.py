"""Hawkes process for tick clustering detection."""
import numpy as np
from typing import List, Tuple, Optional
from scipy.optimize import minimize
from collections import deque


class HawkesProcess:
    """Self-exciting Hawkes process for tick clustering."""
    
    def __init__(
        self,
        kernel: str = "exponential",
        window_seconds: float = 60.0
    ):
        """
        Initialize Hawkes process.
        
        Args:
            kernel: Kernel type ('exponential' or 'power_law')
            window_seconds: Time window for analysis
        """
        self.kernel = kernel
        self.window_seconds = window_seconds
        
        # Parameters (to be estimated)
        self.mu = 1.0  # Background intensity
        self.alpha = 0.5  # Self-excitation magnitude
        self.beta = 1.0  # Decay rate
        
        # Event history
        self.event_times: deque = deque(maxlen=10000)
        
    def add_event(self, timestamp: float) -> None:
        """
        Add event (tick) to history.
        
        Args:
            timestamp: Event timestamp
        """
        self.event_times.append(timestamp)
        
        # Remove old events outside window
        current_time = timestamp
        cutoff_time = current_time - self.window_seconds
        
        while self.event_times and self.event_times[0] < cutoff_time:
            self.event_times.popleft()
            
    def exponential_kernel(self, t: float) -> float:
        """
        Exponential decay kernel.
        
        Args:
            t: Time since event
            
        Returns:
            Kernel value
        """
        if t < 0:
            return 0.0
        return self.alpha * self.beta * np.exp(-self.beta * t)
        
    def power_law_kernel(self, t: float, c: float = 1.0, p: float = 2.0) -> float:
        """
        Power law kernel.
        
        Args:
            t: Time since event
            c: Scaling parameter
            p: Power parameter
            
        Returns:
            Kernel value
        """
        if t < 0:
            return 0.0
        return self.alpha / ((t + c) ** p)
        
    def calculate_intensity(self, t: float) -> float:
        """
        Calculate conditional intensity at time t.
        
        Args:
            t: Time point
            
        Returns:
            Intensity value
        """
        intensity = self.mu
        
        for event_time in self.event_times:
            if event_time < t:
                dt = t - event_time
                if self.kernel == "exponential":
                    intensity += self.exponential_kernel(dt)
                else:
                    intensity += self.power_law_kernel(dt)
                    
        return intensity
        
    def estimate_parameters(self, timestamps: np.ndarray) -> Tuple[float, float, float]:
        """
        Estimate Hawkes process parameters using MLE.
        
        Args:
            timestamps: Array of event timestamps
            
        Returns:
            Tuple of (mu, alpha, beta)
        """
        def negative_log_likelihood(params):
            """Negative log-likelihood function."""
            mu, alpha, beta = params
            
            if mu <= 0 or alpha <= 0 or beta <= 0 or alpha >= beta:
                return 1e10
                
            n = len(timestamps)
            T = timestamps[-1] - timestamps[0]
            
            # Log-likelihood calculation
            ll = 0.0
            
            # Sum over all events
            for i in range(n):
                intensity = mu
                for j in range(i):
                    dt = timestamps[i] - timestamps[j]
                    intensity += alpha * beta * np.exp(-beta * dt)
                    
                if intensity > 0:
                    ll += np.log(intensity)
                else:
                    return 1e10
                    
            # Compensator term
            compensator = mu * T
            for i in range(n):
                for j in range(i):
                    dt = timestamps[i] - timestamps[j]
                    compensator += alpha * (1 - np.exp(-beta * dt))
                    
            ll -= compensator
            
            return -ll
            
        # Initial guess
        x0 = [1.0, 0.5, 1.0]
        
        # Optimize
        result = minimize(
            negative_log_likelihood,
            x0,
            method='L-BFGS-B',
            bounds=[(0.01, 10), (0.01, 5), (0.01, 10)]
        )
        
        if result.success:
            self.mu, self.alpha, self.beta = result.x
            return self.mu, self.alpha, self.beta
        else:
            return self.mu, self.alpha, self.beta
            
    def predict_next_event_time(self, current_time: float, confidence: float = 0.5) -> float:
        """
        Predict time of next event.
        
        Args:
            current_time: Current time
            confidence: Confidence level (0-1)
            
        Returns:
            Predicted time until next event
        """
        current_intensity = self.calculate_intensity(current_time)
        
        if current_intensity <= 0:
            return float('inf')
            
        # Expected time to next event
        expected_time = 1.0 / current_intensity
        
        return expected_time
        
    def detect_clustering(self, threshold_multiplier: float = 1.5) -> bool:
        """
        Detect if events are clustering.
        
        Args:
            threshold_multiplier: Multiplier for clustering threshold
            
        Returns:
            True if clustering detected
        """
        if len(self.event_times) < 10:
            return False
            
        current_time = self.event_times[-1]
        current_intensity = self.calculate_intensity(current_time)
        
        # Compare to background intensity
        return current_intensity > (self.mu * threshold_multiplier)
        
    def get_branching_ratio(self) -> float:
        """
        Get branching ratio (stability measure).
        
        Returns:
            Branching ratio (< 1 is stable)
        """
        if self.beta == 0:
            return float('inf')
        return self.alpha / self.beta
        
    def is_stable(self) -> bool:
        """Check if process is stable (non-explosive)."""
        return self.get_branching_ratio() < 1.0


class TickClusteringDetector:
    """Detect tick clustering patterns for trading signals."""
    
    def __init__(self, window_seconds: float = 60.0, intensity_threshold: float = 1.5):
        """
        Initialize clustering detector.
        
        Args:
            window_seconds: Analysis window in seconds
            intensity_threshold: Threshold for high intensity
        """
        self.hawkes = HawkesProcess(window_seconds=window_seconds)
        self.intensity_threshold = intensity_threshold
        self.intensity_history: deque = deque(maxlen=1000)
        
    def add_tick(self, timestamp: float) -> None:
        """Add tick event."""
        self.hawkes.add_event(timestamp)
        
        # Calculate and store intensity
        intensity = self.hawkes.calculate_intensity(timestamp)
        self.intensity_history.append(intensity)
        
    def is_high_intensity(self) -> bool:
        """Check if current intensity is high."""
        if not self.intensity_history:
            return False
            
        current_intensity = self.intensity_history[-1]
        return current_intensity > (self.hawkes.mu * self.intensity_threshold)
        
    def get_intensity_percentile(self, percentile: float = 95) -> float:
        """Get intensity percentile."""
        if not self.intensity_history:
            return 0.0
            
        intensities = np.array(self.intensity_history)
        return np.percentile(intensities, percentile)
        
    def is_clustering_phase(self) -> bool:
        """Check if market is in clustering phase."""
        return self.hawkes.detect_clustering(self.intensity_threshold)
