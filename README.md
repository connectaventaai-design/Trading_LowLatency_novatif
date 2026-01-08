# HFT GOLD Trading System - Production Ready

A state-of-the-art High-Frequency Trading (HFT) system for GOLD/XAUUSD with MetaTrader 5 integration. This system combines advanced market microstructure analysis, machine learning, and ultra-low latency execution for professional trading.

## 🚀 Key Features

### Advanced Market Analysis
- **VPIN (Volume-Synchronized Probability of Informed Trading)**: Detect toxic order flow
- **Bid-Ask Spread Regime Classification**: Identify liquidity conditions
- **Tick Direction Entropy Analysis**: Measure market uncertainty
- **Order Book Imbalance Detection**: Capture supply/demand dynamics

### Hybrid Intelligence Engine
- **Deep Learning**: LSTM and Transformer models for price prediction
- **Statistical Analysis**: Kalman Filter, Adaptive MAs, Z-score normalization
- **Regime Detection**: Hidden Markov Models for market state identification
- **Hawkes Process**: Tick clustering detection for order flow analysis

### Ultra-Low Latency Architecture
- Async execution pipeline targeting <10ms order execution
- Connection pooling for MT5 API
- Memory-mapped tick data buffers
- JIT compilation with Numba for critical paths
- Pre-calculated order parameters

### Comprehensive Risk Management
- **3 Risk Modes**: Conservative, Moderate, Aggressive
- Real-time P&L tracking with millisecond precision
- Dynamic position sizing based on ATR volatility
- Maximum drawdown protection with auto-stop
- Emergency shutdown capability

### Professional Trading Infrastructure
- Multi-timeframe analysis (tick, 30s-2min, 5-15min)
- Backtesting engine with realistic slippage modeling
- Real-time web dashboard with WebSocket streaming
- Structured logging and performance monitoring
- SQLite database for trade history

## 📋 Requirements

- **Python**: 3.10 or higher
- **MetaTrader 5**: Latest version installed
- **RAM**: Minimum 8GB, 16GB+ recommended
- **CPU**: Multi-core processor (4+ cores recommended)
- **OS**: Windows 10/11 (for MT5), Linux/Mac (with Wine/remote MT5)
- **Network**: Low-latency connection to MT5 broker

## 🔧 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/connectaventaai-design/Trading_LowLatency_novatif.git
cd Trading_LowLatency_novatif

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
```

### 2. Configuration

Edit `.env` file with your MT5 credentials:

```bash
MT5_ACCOUNT=12345678
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Server
SYMBOL=XAUUSD
RISK_MODE=moderate
PAPER_TRADING=true
```

### 3. Run the System

```bash
# Start trading (paper trading mode by default)
python main.py

# Run backtest
python backtest_runner.py

# Train ML models
python train_models.py
```

## 📊 Architecture

```
trading_system/
├── core/           # MT5 connector, order executor, position manager
├── features/       # Microstructure analysis, technical indicators
├── models/         # LSTM, Transformer, Kalman Filter
├── strategy/       # Signal generation, entry/exit logic
├── risk/           # Risk management, position sizing
├── backtesting/    # Backtesting engine, performance metrics
├── dashboard/      # Web dashboard (FastAPI + WebSocket)
└── utils/          # Logging, monitoring, database
```

## 🎯 Trading Strategy

### 3-Layer Hybrid Approach

1. **Tick-level layer** (microseconds to seconds): Scalping momentum bursts
2. **Short-term layer** (30s-2min): Primary directional moves (MAIN FOCUS)
3. **Medium-term layer** (5-15min): Trend continuation plays

### Entry Conditions
- Minimum signal strength threshold
- Regime confirmation
- Avoidance of high VPIN (toxic flow)
- Spread compression preference
- Order book imbalance confirmation (optional)

### Exit Conditions
- Dynamic targets based on ATR
- Time-based exits
- Profit target and stop-loss
- Breakeven adjustment
- Partial position closes

## 📈 Performance Metrics

The system tracks:
- **Sharpe Ratio**: Risk-adjusted returns
- **Sortino Ratio**: Downside risk-adjusted returns
- **Calmar Ratio**: Return vs. max drawdown
- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Gross profit / gross loss
- **Maximum Drawdown**: Peak-to-trough decline
- **Execution Latency**: Order execution speed

## 🔒 Risk Management

### Risk Modes

| Mode | Risk/Trade | Max Positions | Daily Loss Limit | Max Drawdown |
|------|-----------|---------------|------------------|--------------|
| Conservative | 0.5% | 2 | 2% | 5% |
| Moderate | 1.0% | 3 | 5% | 10% |
| Aggressive | 2.0% | 5 | 10% | 15% |

### Safety Features
- Real-time P&L monitoring
- Automatic position closure on limit breach
- Emergency shutdown button
- Daily loss limits with auto-stop
- Maximum position size enforcement

## 🖥️ Web Dashboard

Access the dashboard at `http://localhost:8000` when running:

- **Live Trading View**: Real-time positions, P&L, equity curve
- **Analytics**: Performance metrics, risk metrics, signal strength
- **Control Panel**: Start/stop trading, risk mode selection, emergency controls

## 📚 Documentation

- [Installation Guide](INSTALLATION.md) - Detailed setup instructions
- [Configuration Guide](CONFIGURATION.md) - All configuration parameters
- [Strategy Documentation](STRATEGY.md) - Trading strategy details
- [API Documentation](API.md) - REST API and WebSocket endpoints
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [Backtesting Guide](BACKTESTING.md) - Backtesting methodology

## ⚠️ Important Notes

### Paper Trading
By default, the system runs in **paper trading mode**. Set `PAPER_TRADING=false` in `.env` only after thorough testing.

### Risk Disclaimer
Trading financial instruments involves substantial risk of loss. This software is provided for educational and research purposes. The authors are not responsible for any financial losses incurred.

### Data Requirements
- Historical tick data recommended for ML model training
- Minimum 6 months of data for robust backtesting
- Real-time data feed required for live trading

## 🛠️ Development

### Running Tests
```bash
pytest trading_system/tests/
```

### Code Quality
```bash
# Format code
black trading_system/

# Lint code
ruff check trading_system/

# Type checking
mypy trading_system/
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please read CONTRIBUTING.md for guidelines.

## 📧 Support

For issues and questions, please open an issue on GitHub.

## 🙏 Acknowledgments

- MetaTrader 5 for the trading platform
- Python scientific computing community
- HFT research community

---

**Built with ❤️ for professional traders**
