# Backtesting Guide

## Overview

The HFT GOLD Trading System includes a comprehensive backtesting framework to validate trading strategies before live deployment.

## Data Requirements

### Historical Data

**Minimum Requirements**:
- 6 months of historical data
- Tick-level data preferred (1-second bars minimum)
- Include bid, ask, last price, and volume

**Recommended**:
- 12+ months of data
- Tick-level data with millisecond timestamps
- Level 2 market data (optional)

### Data Sources

1. **MT5 Historical Data**
   - Available through MT5 terminal
   - Limited history (typically 1-3 months tick data)

2. **Commercial Data Providers**
   - Dukascopy
   - HistData.com
   - QuantConnect
   - AlgoSeek

3. **Broker Historical Data**
   - Request from your broker
   - Usually available for clients

## Data Preparation

### Downloading Data from MT5

```python
import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd

# Initialize MT5
mt5.initialize()

# Download tick data
ticks = mt5.copy_ticks_range("XAUUSD", 
    datetime(2023, 1, 1), 
    datetime(2023, 12, 31), 
    mt5.COPY_TICKS_ALL
)

# Convert to DataFrame
df = pd.DataFrame(ticks)
df['time'] = pd.to_datetime(df['time'], unit='s')
df.to_parquet('data/xauusd_ticks_2023.parquet')
```

### Data Cleaning

```python
# Remove outliers
def remove_outliers(df, column, std_threshold=5):
    mean = df[column].mean()
    std = df[column].std()
    df = df[
        (df[column] > mean - std_threshold * std) & 
        (df[column] < mean + std_threshold * std)
    ]
    return df

# Remove bad ticks (zero prices, excessive spreads)
df = df[df['bid'] > 0]
df = df[df['ask'] > 0]
df = df[(df['ask'] - df['bid']) < df['bid'] * 0.01]  # Max 1% spread
```

## Running Backtests

### Basic Backtest

```bash
python backtest_runner.py \
    --start-date 2023-01-01 \
    --end-date 2023-12-31 \
    --initial-capital 10000 \
    --risk-mode moderate
```

### Advanced Backtest with Parameters

```bash
python backtest_runner.py \
    --start-date 2023-01-01 \
    --end-date 2023-12-31 \
    --initial-capital 10000 \
    --risk-mode moderate \
    --slippage-pips 2 \
    --commission 7 \
    --output results/backtest_2023.json
```

## Slippage Modeling

### Realistic Slippage

The backtesting engine includes realistic slippage modeling:

1. **Bid-Ask Spread**: Always crossed (you buy at ask, sell at bid)
2. **Market Impact**: Proportional to order size
3. **Latency**: Simulated execution delay

```python
# Slippage calculation
base_slippage = spread / 2
volume_impact = order_size * market_impact_coefficient
latency_slippage = price_movement_during_latency
total_slippage = base_slippage + volume_impact + latency_slippage
```

### Slippage Scenarios

- **Best Case**: 0.5 pips (tight spread, small order)
- **Average Case**: 2 pips (normal conditions)
- **Worst Case**: 5+ pips (wide spread, large order, high volatility)

## Transaction Costs

### Commission Structure

```yaml
# Typical MT5 broker commissions
per_lot: 7  # USD per lot
per_million: 50  # USD per million in volume
```

### Total Cost Calculation

```python
transaction_cost = (
    commission_per_lot * volume +
    spread_cost +
    slippage_cost
)
```

## Performance Metrics

### Key Metrics

1. **Total Return**: (Final Capital - Initial Capital) / Initial Capital
2. **Sharpe Ratio**: (Avg Return - Risk-Free Rate) / Std Dev of Returns
3. **Sortino Ratio**: Similar to Sharpe, but only considers downside volatility
4. **Calmar Ratio**: Annual Return / Max Drawdown
5. **Win Rate**: Winning Trades / Total Trades
6. **Profit Factor**: Gross Profit / Gross Loss
7. **Maximum Drawdown**: Largest peak-to-trough decline
8. **Average Trade Duration**: Mean time in position

### Example Results

```
=== Backtest Results ===
Period: 2023-01-01 to 2023-12-31
Initial Capital: $10,000.00
Final Capital: $15,234.56
Total Return: 52.35%

Performance Metrics:
- Sharpe Ratio: 2.14
- Sortino Ratio: 3.21
- Calmar Ratio: 5.23
- Maximum Drawdown: 8.45%

Trading Statistics:
- Total Trades: 1,250
- Winning Trades: 687 (55%)
- Losing Trades: 563 (45%)
- Profit Factor: 1.85
- Average Win: $15.32
- Average Loss: -$8.76
- Best Trade: $234.50
- Worst Trade: -$87.23
- Average Trade Duration: 1m 45s
```

## Walk-Forward Optimization

### Purpose

Prevent overfitting by testing on unseen data periods.

### Process

1. **Train Period**: 180 days
2. **Test Period**: 30 days
3. **Step**: 30 days

```python
# Walk-forward optimization
train_periods = []
test_periods = []

start = datetime(2023, 1, 1)
end = datetime(2023, 12, 31)

current = start
while current < end:
    train_end = current + timedelta(days=180)
    test_end = train_end + timedelta(days=30)
    
    train_periods.append((current, train_end))
    test_periods.append((train_end, test_end))
    
    current += timedelta(days=30)
```

### Results Analysis

```
Walk-Forward Analysis:
Window 1: Train Sharpe 2.5, Test Sharpe 2.1 ✓
Window 2: Train Sharpe 2.3, Test Sharpe 2.0 ✓
Window 3: Train Sharpe 2.7, Test Sharpe 1.8 ⚠
Window 4: Train Sharpe 2.4, Test Sharpe 2.2 ✓
...

Average Train Sharpe: 2.47
Average Test Sharpe: 2.03
Degradation: 17.8% (acceptable)
```

## Validation Techniques

### 1. Out-of-Sample Testing

Reserve 20-30% of data for out-of-sample testing.

### 2. Monte Carlo Simulation

Randomly shuffle trade order to test robustness:

```python
# 1000 Monte Carlo runs
original_trades = backtest.trades
monte_carlo_results = []

for i in range(1000):
    shuffled = shuffle(original_trades)
    result = calculate_metrics(shuffled)
    monte_carlo_results.append(result)

# Confidence intervals
sharpe_95_ci = percentile(monte_carlo_results, [2.5, 97.5])
```

### 3. Parameter Sensitivity

Test strategy across parameter ranges:

```python
# Test ATR multipliers
for atr_mult in [1.0, 1.5, 2.0, 2.5, 3.0]:
    result = backtest(atr_multiplier=atr_mult)
    print(f"ATR {atr_mult}: Sharpe {result.sharpe}")
```

## Common Pitfalls

### 1. Look-Ahead Bias

❌ **Wrong**: Using future data in indicators
✓ **Correct**: Only use data available at decision time

### 2. Survivorship Bias

❌ **Wrong**: Testing only on current market conditions
✓ **Correct**: Include various market regimes

### 3. Overfitting

❌ **Wrong**: Optimizing for maximum backtest performance
✓ **Correct**: Use walk-forward, out-of-sample validation

### 4. Unrealistic Assumptions

❌ **Wrong**: No slippage, instant fills, zero spread
✓ **Correct**: Model realistic execution conditions

### 5. Data Quality Issues

❌ **Wrong**: Ignoring outliers, bad ticks
✓ **Correct**: Clean and validate data

## Interpreting Results

### Good Backtest Characteristics

✓ Sharpe Ratio > 1.5
✓ Win Rate > 50% (for this strategy)
✓ Profit Factor > 1.5
✓ Max Drawdown < 15%
✓ Consistent performance across different periods
✓ Test performance close to train performance

### Warning Signs

⚠ Sharpe Ratio > 3.0 (too good, likely overfitting)
⚠ Win Rate > 80% (unrealistic)
⚠ Large discrepancy between train and test
⚠ Performance heavily dependent on one trade
⚠ No losing months (overfitting)

### Red Flags

❌ Negative Sharpe Ratio
❌ Max Drawdown > 30%
❌ Profit Factor < 1.0
❌ Large slippage sensitivity

## Comparing Strategies

### Strategy A vs Strategy B

```
Metric          Strategy A    Strategy B
-----------------------------------------------
Sharpe Ratio    2.10          1.85
Max Drawdown    8.5%          6.2%
Win Rate        55%           48%
Profit Factor   1.85          2.10
Avg Duration    1m 45s        3m 20s
```

**Analysis**: 
- Strategy A: Better Sharpe, higher win rate, faster trades
- Strategy B: Lower drawdown, better profit factor, longer holds
- **Choice depends on risk preference**

## Reporting

### Generate HTML Report

```bash
python backtest_runner.py --generate-report
```

### Report Contents

1. Executive Summary
2. Performance Metrics
3. Equity Curve Chart
4. Drawdown Chart
5. Trade Distribution
6. Monthly Returns Heatmap
7. Trade-by-Trade List
8. Parameter Sensitivity Analysis

## Next Steps After Backtesting

1. **If results are good**:
   - Run walk-forward optimization
   - Test on out-of-sample data
   - Monte Carlo validation
   - Paper trading for 2+ weeks

2. **If results are poor**:
   - Analyze losing trades
   - Check for implementation errors
   - Adjust parameters
   - Consider strategy redesign

3. **If results are suspicious**:
   - Check for look-ahead bias
   - Verify data quality
   - Test with different slippage assumptions
   - Simplify strategy

---

**Remember**: Good backtest ≠ Good live performance. Always validate with paper trading!
