"""System performance monitoring."""
import time
import psutil
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SystemMetrics:
    """System resource metrics."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    network_sent_mb: float
    network_recv_mb: float
    thread_count: int
    
    
@dataclass
class PerformanceMetrics:
    """Trading performance metrics."""
    timestamp: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_pnl_per_trade: float
    max_drawdown: float
    sharpe_ratio: Optional[float]
    latency_avg_ms: float
    latency_p95_ms: float
    latency_p99_ms: float


class PerformanceMonitor:
    """Monitor system and trading performance."""
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.process = psutil.Process()
        self.start_time = time.time()
        self.latency_measurements: list[float] = []
        self.max_latency_samples = 10000
        
        # Network counters
        self._network_io_start = psutil.net_io_counters()
        
    def get_system_metrics(self) -> SystemMetrics:
        """
        Get current system resource metrics.
        
        Returns:
            SystemMetrics object
        """
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        return SystemMetrics(
            timestamp=time.time(),
            cpu_percent=self.process.cpu_percent(interval=0.1),
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            memory_available_mb=memory.available / (1024 * 1024),
            disk_usage_percent=disk.percent,
            network_sent_mb=(network.bytes_sent - self._network_io_start.bytes_sent) / (1024 * 1024),
            network_recv_mb=(network.bytes_recv - self._network_io_start.bytes_recv) / (1024 * 1024),
            thread_count=self.process.num_threads(),
        )
        
    def record_latency(self, latency_ms: float) -> None:
        """
        Record a latency measurement.
        
        Args:
            latency_ms: Latency in milliseconds
        """
        self.latency_measurements.append(latency_ms)
        
        # Keep only recent samples
        if len(self.latency_measurements) > self.max_latency_samples:
            self.latency_measurements = self.latency_measurements[-self.max_latency_samples:]
            
    def get_latency_stats(self) -> Dict[str, float]:
        """
        Get latency statistics.
        
        Returns:
            Dictionary with latency statistics
        """
        if not self.latency_measurements:
            return {
                'avg': 0.0,
                'min': 0.0,
                'max': 0.0,
                'p50': 0.0,
                'p95': 0.0,
                'p99': 0.0,
            }
            
        sorted_latencies = sorted(self.latency_measurements)
        n = len(sorted_latencies)
        
        return {
            'avg': sum(sorted_latencies) / n,
            'min': sorted_latencies[0],
            'max': sorted_latencies[-1],
            'p50': sorted_latencies[int(n * 0.50)],
            'p95': sorted_latencies[int(n * 0.95)],
            'p99': sorted_latencies[int(n * 0.99)],
        }
        
    def get_uptime_seconds(self) -> float:
        """Get system uptime in seconds."""
        return time.time() - self.start_time
        
    def get_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory information."""
        mem_info = self.process.memory_info()
        return {
            'rss_mb': mem_info.rss / (1024 * 1024),
            'vms_mb': mem_info.vms / (1024 * 1024),
            'percent': self.process.memory_percent(),
        }
        
    def reset_latency_stats(self) -> None:
        """Reset latency measurements."""
        self.latency_measurements.clear()


class LatencyTracker:
    """Context manager for tracking operation latency."""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        """
        Initialize latency tracker.
        
        Args:
            monitor: PerformanceMonitor instance
            operation_name: Name of the operation being tracked
        """
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time: Optional[float] = None
        
    def __enter__(self):
        """Start tracking."""
        self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop tracking and record latency."""
        if self.start_time is not None:
            latency_ms = (time.perf_counter() - self.start_time) * 1000
            self.monitor.record_latency(latency_ms)
            
    async def __aenter__(self):
        """Async context manager enter."""
        self.start_time = time.perf_counter()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.start_time is not None:
            latency_ms = (time.perf_counter() - self.start_time) * 1000
            self.monitor.record_latency(latency_ms)


# Global monitor instance
_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor
