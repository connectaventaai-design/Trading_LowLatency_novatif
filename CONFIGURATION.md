# Configuration Guide

This guide explains all configuration options for the HFT GOLD Trading System.

## Configuration Files

The system uses multiple configuration files for different aspects:

1. **`.env`** - Environment variables (credentials, paths)
2. **`config/config.yaml`** - Main system configuration
3. **`config/mt5_config.yaml`** - MT5 connection settings
4. **`config/risk_profiles.yaml`** - Risk management profiles
5. **`config/strategy_params.yaml`** - Trading strategy parameters

## Environment Variables (.env)

### MT5 Connection

```bash
# MT5 Account Credentials
MT5_ACCOUNT=12345678
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Demo

# Trading Symbol
SYMBOL=XAUUSD
TIMEFRAME=M1
MAGIC_NUMBER=123456
```

**MT5_ACCOUNT**: Your MT5 account number
**MT5_PASSWORD**: Your MT5 account password
**MT5_SERVER**: MT5 server name (exactly as shown in terminal)
**SYMBOL**: Trading symbol (XAUUSD for Gold)
**MAGIC_NUMBER**: Unique identifier for orders (1-999999)

### Risk Management

```bash
RISK_MODE=moderate  # conservative, moderate, aggressive
MAX_DAILY_LOSS=1000  # USD
MAX_DRAWDOWN_PERCENT=10.0
AUTO_STOP_ON_DRAWDOWN=true
```

**RISK_MODE**: Selects risk profile (conservative/moderate/aggressive)
**MAX_DAILY_LOSS**: Maximum daily loss in account currency
**MAX_DRAWDOWN_PERCENT**: Maximum drawdown before auto-stop
**AUTO_STOP_ON_DRAWDOWN**: Enable automatic shutdown on drawdown breach

### System Settings

```bash
# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/trading.log

# Database
DB_PATH=data/trading.db
REDIS_HOST=localhost
REDIS_PORT=6379
USE_REDIS=false

# Performance
CPU_AFFINITY=0,1,2,3
JIT_ENABLED=true
OPTIMIZATION_LEVEL=3
```

### Trading Mode

```bash
PAPER_TRADING=true  # CRITICAL: Set to false only for live trading
TIMEZONE=UTC
```

## Main Configuration (config/config.yaml)

### System Settings

```yaml
system:
  name: "HFT GOLD Trading System"
  version: "1.0.0"
  timezone: "UTC"
  paper_trading: true
```

### Trading Settings

```yaml
trading:
  symbol: "XAUUSD"
  magic_number: 123456
  max_slippage_points: 10
  min_profit_points: 5
```

**max_slippage_points**: Maximum acceptable slippage in points
**min_profit_points**: Minimum profit to close position

### Timeframe Configuration

```yaml
timeframes:
  tick_level:
    enabled: true
    window_seconds: 1
  short_term:
    enabled: true
    window_seconds: 120
    primary: true
  medium_term:
    enabled: true
    window_seconds: 900
```

### Execution Settings

```yaml
execution:
  target_latency_ms: 10
  connection_pool_size: 5
  order_timeout_seconds: 30
  max_retries: 3
  retry_delay_ms: 100
```

**target_latency_ms**: Target execution latency (for monitoring)
**connection_pool_size**: Number of pre-established connections
**max_retries**: Maximum order retry attempts

## Risk Profiles (config/risk_profiles.yaml)

### Conservative Mode

```yaml
conservative:
  name: "Conservative Mode"
  risk_per_trade_percent: 0.5
  max_concurrent_positions: 2
  max_daily_loss_percent: 2.0
  max_drawdown_percent: 5.0
  position_size_multiplier: 0.5
  take_profit_atr_multiplier: 2.0
  stop_loss_atr_multiplier: 1.5
```

**Best for**: Risk-averse traders, beginners, small accounts

### Moderate Mode (Default)

```yaml
moderate:
  name: "Moderate Mode"
  risk_per_trade_percent: 1.0
  max_concurrent_positions: 3
  max_daily_loss_percent: 5.0
  max_drawdown_percent: 10.0
  position_size_multiplier: 1.0
  take_profit_atr_multiplier: 3.0
  stop_loss_atr_multiplier: 2.0
```

**Best for**: Balanced risk/reward, intermediate traders

### Aggressive Mode

```yaml
aggressive:
  name: "Aggressive Mode"
  risk_per_trade_percent: 2.0
  max_concurrent_positions: 5
  max_daily_loss_percent: 10.0
  max_drawdown_percent: 15.0
  position_size_multiplier: 1.5
  take_profit_atr_multiplier: 4.0
  stop_loss_atr_multiplier: 2.5
```

**Best for**: Experienced traders, larger accounts, high risk tolerance

### Risk Parameter Explanations

- **risk_per_trade_percent**: Percentage of equity risked per trade
- **max_concurrent_positions**: Maximum number of simultaneous positions
- **max_daily_loss_percent**: Daily loss limit as % of equity
- **max_drawdown_percent**: Maximum drawdown before auto-stop
- **position_size_multiplier**: Multiplier for calculated position size
- **take_profit_atr_multiplier**: TP distance as multiple of ATR
- **stop_loss_atr_multiplier**: SL distance as multiple of ATR

## Strategy Parameters (config/strategy_params.yaml)

### Technical Indicators

```yaml
indicators:
  atr:
    period: 14
    smoothing: "ema"
  ema_fast: 12
  ema_slow: 26
  rsi:
    period: 14
    overbought: 70
    oversold: 30
```

### Microstructure Settings

```yaml
microstructure:
  vpin:
    bucket_size: 50
    window_size: 50
    toxicity_threshold: 0.7
  spread_regime:
    tight_threshold_pips: 2.0
    wide_threshold_pips: 5.0
  entropy:
    window_size: 100
    high_entropy_threshold: 0.8
```

**VPIN Settings**:
- **bucket_size**: Ticks per volume bucket
- **window_size**: Number of buckets in moving window
- **toxicity_threshold**: VPIN threshold for toxic flow (0-1)

### Signal Generation

```yaml
signals:
  tick_layer:
    enabled: true
    weight: 0.2
    min_confidence: 0.6
  short_term_layer:
    enabled: true
    weight: 0.5
    min_confidence: 0.7
  medium_term_layer:
    enabled: true
    weight: 0.3
    min_confidence: 0.65
```

**Signal Weights**: Must sum to 1.0 across enabled layers

### Entry Conditions

```yaml
entry:
  min_signal_strength: 0.7
  require_regime_confirmation: true
  avoid_high_vpin: true
  wait_for_spread_compression: true
  max_spread_multiplier: 1.5
```

### Exit Conditions

```yaml
exit:
  use_dynamic_targets: true
  time_based_exit_enabled: true
  max_hold_minutes: 30
  profit_target_atr_multiplier: 3.0
  stop_loss_atr_multiplier: 2.0
```

## Best Practices

### For Beginners

```bash
RISK_MODE=conservative
PAPER_TRADING=true
MAX_DAILY_LOSS=100
```

Start with:
- Conservative risk mode
- Paper trading enabled
- Low daily loss limits
- Monitor for at least 1 month

### For Intermediate Traders

```bash
RISK_MODE=moderate
PAPER_TRADING=true  # Start with paper trading
MAX_DAILY_LOSS=500
```

Progress to:
- Moderate risk mode
- Validate with paper trading first
- Gradually increase limits

### For Advanced Traders

```bash
RISK_MODE=aggressive
MAX_DAILY_LOSS=2000
MAX_DRAWDOWN_PERCENT=15.0
```

After extensive testing:
- Aggressive mode if comfortable
- Higher limits based on account size
- Continuous monitoring essential

## Production Settings Checklist

Before going live:

- [ ] MT5 credentials verified and correct
- [ ] Risk mode appropriate for account size
- [ ] All limits set conservatively
- [ ] Backtests completed successfully
- [ ] Paper trading tested for minimum 1 week
- [ ] Emergency procedures understood
- [ ] Monitoring system active
- [ ] Logging enabled and working
- [ ] Database backup configured

## Tuning for Performance

### High-Frequency Trading

For maximum speed:
```yaml
execution:
  target_latency_ms: 5
  connection_pool_size: 10
```

```bash
JIT_ENABLED=true
OPTIMIZATION_LEVEL=3
CPU_AFFINITY=0,1,2,3  # Dedicated cores
```

### Stable/Conservative Trading

For reliability:
```yaml
execution:
  target_latency_ms: 50
  max_retries: 5
```

```bash
LOG_LEVEL=DEBUG  # More logging
```

## Common Issues

### "Risk limits too strict, no trades executed"

**Solution**: Adjust `min_signal_strength` or risk mode

### "Too many positions opened"

**Solution**: Decrease `max_concurrent_positions`

### "Daily loss limit hit too quickly"

**Solution**: 
- Increase `MAX_DAILY_LOSS`
- Or switch to more conservative risk mode

### "High slippage"

**Solution**:
- Decrease `max_slippage_points`
- Check broker execution quality
- Consider different trading hours

## Monitoring Configuration Changes

All configuration changes are logged. Check logs:

```bash
tail -f logs/trading.log | grep "config"
```

## Reloading Configuration

The system requires restart for most configuration changes. Some runtime changes:

```python
# Change risk mode via API (if dashboard running)
curl -X POST http://localhost:8000/risk/mode -d '{"mode": "conservative"}'
```

---

**Warning**: Always test configuration changes in paper trading mode first!
