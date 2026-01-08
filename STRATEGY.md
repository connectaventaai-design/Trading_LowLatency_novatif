# Trading Strategy Documentation

## Overview

The HFT GOLD Trading System implements a sophisticated **3-layer hybrid approach** combining high-frequency scalping with directional trading. The system leverages advanced market microstructure analysis, machine learning, and statistical models to identify and exploit trading opportunities in the GOLD/XAUUSD market.

## Strategy Architecture

### Multi-Timeframe Layers

#### 1. Tick-Level Layer (Microseconds to Seconds)
**Purpose**: Capture ultra-short-term momentum bursts

**Features**:
- Real-time tick processing with <10ms latency
- Order flow analysis using Hawkes process
- Tick clustering detection
- Momentum burst identification

**Entry Criteria**:
- Significant tick clustering detected
- Order flow intensity > threshold
- Spread compression
- Low VPIN (non-toxic flow)

**Exit Criteria**:
- Momentum reversal
- Fixed tick profit target (5-10 ticks)
- Time-based exit (1-3 seconds)

#### 2. Short-Term Layer (30 seconds to 2 minutes) - PRIMARY FOCUS
**Purpose**: Exploit directional moves during high-conviction periods

**Features**:
- Multi-indicator signal aggregation
- Regime-aware parameter adjustment
- Microstructure-based entry timing
- ATR-based dynamic targets

**Entry Criteria**:
- Signal strength > 0.7 (configurable)
- Regime confirmation (trending/high volatility preferred)
- VPIN < 0.7 (avoid toxic flow)
- Spread within normal range
- Optional: Order book imbalance confirmation

**Exit Criteria**:
- Take profit: 3x ATR (default)
- Stop loss: 2x ATR (default)
- Time-based: Maximum 2 minutes
- Trailing stop: 1.5x ATR (if enabled)

#### 3. Medium-Term Layer (5-15 minutes)
**Purpose**: Capture trend continuation and larger moves

**Features**:
- Trend strength analysis
- Volume profile analysis (POC, VAH, VAL)
- Regime persistence detection
- Position pyramiding (optional)

**Entry Criteria**:
- Strong trend signal (trend strength > 0.6)
- Regime stability (low transition probability)
- Volume confirmation
- Price near value area

**Exit Criteria**:
- Take profit: 4x ATR
- Stop loss: 2.5x ATR
- Time-based: Maximum 15 minutes
- Trend reversal signal

## Signal Generation Process

### Step 1: Data Collection
```
Tick Data → Buffer → Feature Extraction
```

### Step 2: Feature Engineering

**Price Features**:
- Returns (1-tick, 5-tick, 1-minute)
- Log returns
- Price momentum
- Z-score normalized prices

**Volatility Features**:
- ATR (14-period)
- Tick-level volatility
- Volatility regime classification

**Microstructure Features**:
- VPIN (toxicity measure)
- Spread regime (tight/normal/wide)
- Tick direction entropy
- Order book imbalance

**Volume Features**:
- Volume ratio
- Volume profile (POC, VAH, VAL)
- Tick volume intensity

**Regime Features**:
- HMM state (trending/ranging/high-vol/consolidation)
- Regime transition probabilities
- Hawkes intensity (clustering)

### Step 3: Signal Aggregation

Signals from each layer are combined using weighted averaging:

```
Final Signal = (w1 * S_tick + w2 * S_short + w3 * S_medium) / (w1 + w2 + w3)

Default weights:
w1 = 0.2 (tick layer)
w2 = 0.5 (short-term layer) ← PRIMARY
w3 = 0.3 (medium-term layer)
```

### Step 4: Entry Timing

**Microstructure-Based Timing**:
1. Wait for spread compression (spread < 75th percentile)
2. Confirm order book imbalance direction
3. Verify VPIN < toxicity threshold
4. Check entropy not too high (avoid random markets)

**Regime-Based Adjustment**:
- **Trending**: Higher position size, wider stops
- **Ranging**: Smaller position size, tighter stops
- **High Volatility**: Reduced position size, wider stops
- **Consolidation**: Minimal trading, tight stops

## Machine Learning Components

### 1. LSTM Price Prediction
**Architecture**:
- Input: Sequence of 60 ticks/bars
- Hidden layers: 2 layers, 128 units each
- Output: Price direction probability

**Training**:
- Walk-forward validation
- Data augmentation (noise injection, time shifting)
- Weekly retraining schedule

### 2. Transformer with Multi-Head Attention
**Purpose**: Capture multi-scale temporal dependencies

**Architecture**:
- 8 attention heads
- 4 transformer layers
- Learns to weight importance of different timeframes

### 3. Kalman Filter
**Purpose**: Real-time noise reduction and state estimation

**Application**:
- Smooth price series
- Estimate hidden states (trend, momentum)
- Adaptive parameter tuning

### 4. Hidden Markov Model (Regime Detection)
**States**: 4 market regimes
1. **Trending**: Persistent directional movement
2. **Ranging**: Mean-reverting behavior
3. **High Volatility**: Large, erratic moves
4. **Consolidation**: Low volatility, tight range

**Usage**:
- Automatic strategy parameter adjustment
- Risk management adaptation
- Trade filtering

## Risk Management Integration

### Position Sizing
```python
position_size = (account_equity * risk_percent) / (atr * atr_multiplier * contract_size)
```

Adjustments:
- Conservative mode: × 0.5
- Moderate mode: × 1.0
- Aggressive mode: × 1.5
- Regime-based: Further adjustment

### Stop Loss Placement
```
SL = entry_price ± (ATR * sl_multiplier)

Conservative: sl_multiplier = 1.5
Moderate: sl_multiplier = 2.0
Aggressive: sl_multiplier = 2.5
```

### Take Profit Placement
```
TP = entry_price ± (ATR * tp_multiplier)

Conservative: tp_multiplier = 2.0
Moderate: tp_multiplier = 3.0
Aggressive: tp_multiplier = 4.0
```

## Innovative Features

### 1. VPIN-Based Flow Toxicity Detection
**Innovation**: Avoid trading during toxic flow periods

**Implementation**:
- Calculate VPIN in real-time
- Filter out trades when VPIN > 0.7
- Reduce position size when 0.5 < VPIN < 0.7

### 2. Hawkes Process Tick Clustering
**Innovation**: Detect and exploit self-exciting price movements

**Application**:
- Predict future tick arrival intensity
- Identify clustering phases
- Time entries during high-intensity periods

### 3. Entropy-Based Uncertainty Measure
**Innovation**: Avoid trading in random/uncertain markets

**Calculation**:
- Shannon entropy of tick direction changes
- High entropy = high randomness = avoid trading

### 4. Adaptive Regime-Based Parameters
**Innovation**: Automatically adjust strategy to market conditions

**Mechanism**:
- HMM detects current regime
- Parameters adjusted based on regime characteristics
- Smooth transitions between regimes

### 5. Spread Compression Entry Timing
**Innovation**: Enter only when liquidity conditions are favorable

**Logic**:
- Calculate spread percentiles
- Wait for spread < 25th percentile
- Minimize transaction costs

## GOLD/XAUUSD Specific Optimizations

### Market Characteristics
- **Volatility Pattern**: Increases during London/NY overlap (8 AM - 12 PM EST)
- **Spread Behavior**: Widens during news events
- **Correlation**: Inverse with USD Index (DXY)

### Optimizations
1. **Volume Weighting**: Higher activity during overlap sessions
2. **News Avoidance**: Pause trading 15 min before, 30 min after major news
3. **Session Filters**: Prefer high-liquidity sessions
4. **Spread Thresholds**: Adjusted for GOLD typical spreads (2-5 pips)

## Performance Expectations

### Conservative Mode
- **Win Rate**: 55-60%
- **Profit Factor**: 1.5-2.0
- **Max Drawdown**: < 5%
- **Monthly Return**: 3-5%

### Moderate Mode
- **Win Rate**: 50-55%
- **Profit Factor**: 1.8-2.5
- **Max Drawdown**: < 10%
- **Monthly Return**: 5-10%

### Aggressive Mode
- **Win Rate**: 45-50%
- **Profit Factor**: 2.0-3.0
- **Max Drawdown**: < 15%
- **Monthly Return**: 10-20%

**Note**: Past performance doesn't guarantee future results.

## Strategy Validation

### Backtesting Requirements
- Minimum 6 months historical data
- Tick-level data preferred
- Include realistic slippage (1-3 pips)
- Transaction costs (spread + commission)

### Walk-Forward Optimization
- Train period: 180 days
- Test period: 30 days
- Step: 30 days
- Minimum 100 trades per test period

### Robustness Tests
- Monte Carlo simulation (1000+ runs)
- Parameter sensitivity analysis
- Different market regimes
- Stress testing (high volatility periods)

## Continuous Improvement

### Model Retraining
- **Frequency**: Weekly
- **Data Window**: Rolling 6 months
- **Validation**: Walk-forward testing
- **Deployment**: Gradual rollout

### Performance Monitoring
- Daily: P&L, win rate, drawdown
- Weekly: Sharpe ratio, strategy metrics
- Monthly: Full performance review
- Quarterly: Strategy revalidation

### Adaptation Mechanisms
- Regime detection updates
- Feature importance tracking
- Signal correlation analysis
- Risk parameter adjustment

---

**Remember**: This strategy requires continuous monitoring and should never be left completely unattended. Always start with paper trading and thoroughly validate before live deployment.
