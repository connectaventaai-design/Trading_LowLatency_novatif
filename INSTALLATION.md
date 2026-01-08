# Installation Guide

This guide provides step-by-step instructions for installing and setting up the HFT GOLD Trading System.

## System Requirements

### Hardware Requirements
- **CPU**: Multi-core processor (4+ cores recommended, 8+ cores optimal)
- **RAM**: Minimum 8GB, 16GB+ recommended for ML models
- **Storage**: 50GB+ free space (for tick data and models)
- **Network**: Low-latency internet connection (< 50ms to broker)

### Software Requirements
- **Operating System**: 
  - Windows 10/11 (recommended for MT5)
  - Linux (Ubuntu 20.04+, requires Wine for MT5)
  - macOS (requires remote MT5 server)
- **Python**: 3.10 or higher
- **MetaTrader 5**: Latest version from broker

### Broker Requirements
- MT5 account with API access enabled
- Low spreads on XAUUSD (< 3 pips average)
- Good execution quality (< 100ms average)
- Sufficient margin for trading

## Installation Steps

### 1. Install Python 3.10+

#### Windows
Download and install from [python.org](https://www.python.org/downloads/)

```bash
python --version  # Verify installation
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
```

#### macOS
```bash
brew install python@3.10
```

### 2. Install MetaTrader 5

1. Download MT5 from your broker's website
2. Install and log in to your account
3. Ensure the account has API access enabled
4. Note your account number, password, and server name

### 3. Clone the Repository

```bash
git clone https://github.com/connectaventaai-design/Trading_LowLatency_novatif.git
cd Trading_LowLatency_novatif
```

### 4. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### 5. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install core dependencies
pip install -r requirements.txt
```

**Note**: If you encounter issues with TA-Lib installation:

#### Windows
Download and install TA-Lib from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

```bash
pip install TA_Lib‑0.4.26‑cp310‑cp310‑win_amd64.whl
```

#### Linux
```bash
sudo apt-get install build-essential
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
pip install TA-Lib
```

#### macOS
```bash
brew install ta-lib
pip install TA-Lib
```

### 6. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

Required settings in `.env`:

```bash
# MT5 Connection
MT5_ACCOUNT=12345678          # Your MT5 account number
MT5_PASSWORD=your_password    # Your MT5 password
MT5_SERVER=YourBroker-Server  # Your MT5 server name

# Trading Settings
SYMBOL=XAUUSD
RISK_MODE=moderate            # conservative, moderate, or aggressive
PAPER_TRADING=true            # Set to false only after testing

# Paths
LOG_LEVEL=INFO
LOG_FILE=logs/trading.log
DB_PATH=data/trading.db
```

### 7. Create Required Directories

```bash
# Create data directories
mkdir -p trading_system/data
mkdir -p trading_system/logs
mkdir -p trading_system/models_trained
```

### 8. Initialize Database

The database will be created automatically on first run. To manually initialize:

```python
import asyncio
from pathlib import Path
from trading_system.utils.database import TradingDatabase

async def init_db():
    db = TradingDatabase(Path("trading_system/data/trading.db"))
    await db.connect()
    print("Database initialized")
    await db.close()

asyncio.run(init_db())
```

### 9. Test Installation

Run the test suite to verify installation:

```bash
# Run all tests
pytest trading_system/tests/ -v

# Or run a quick system check
python -c "
from trading_system.utils.config_loader import get_config_loader
from trading_system.utils.logger import get_logger
print('✓ Config loader works')
print('✓ Logger works')
print('Installation successful!')
"
```

### 10. Test MT5 Connection

```python
import asyncio
from trading_system.core.mt5_connector import get_mt5_connector

async def test_connection():
    connector = get_mt5_connector()
    connected = await connector.connect()
    if connected:
        print("✓ MT5 connected successfully")
        account = connector.get_account_info()
        if account:
            print(f"  Account: {account.login}")
            print(f"  Balance: {account.balance}")
            print(f"  Equity: {account.equity}")
    else:
        print("✗ MT5 connection failed")
    await connector.disconnect()

asyncio.run(test_connection())
```

## Optional Components

### Redis (Optional, for advanced caching)

If you want to use Redis for caching:

#### Windows
Download and install from: https://github.com/microsoftarchive/redis/releases

#### Linux
```bash
sudo apt install redis-server
sudo systemctl start redis
```

#### macOS
```bash
brew install redis
brew services start redis
```

Enable Redis in `.env`:
```bash
USE_REDIS=true
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Jupyter Notebook (for analysis)

```bash
pip install jupyter notebook
```

## Troubleshooting

### Issue: "MetaTrader5 module not found"

**Solution**: 
```bash
pip install --upgrade MetaTrader5
```

### Issue: "Failed to initialize MT5"

**Solutions**:
1. Ensure MT5 terminal is running
2. Check if terminal is logged in
3. Verify API access is enabled in MT5 settings
4. Run Python as Administrator (Windows)

### Issue: "Failed to connect to MT5 account"

**Solutions**:
1. Verify credentials in `.env`
2. Check server name (copy exactly from MT5)
3. Ensure account allows API access
4. Check if account is demo or live (use correct type)

### Issue: "NumPy/Pandas installation fails"

**Solution**: Install Visual C++ Build Tools (Windows)
Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

### Issue: "Permission denied" on Linux

**Solution**:
```bash
sudo chmod +x main.py
sudo chown -R $USER:$USER .
```

## Performance Optimization

### CPU Affinity (Linux)

To pin the process to specific CPU cores:

```bash
taskset -c 0-3 python main.py
```

### Network Optimization (Linux)

```bash
# Increase socket buffer sizes
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.wmem_max=134217728
sudo sysctl -w net.ipv4.tcp_rmem='4096 87380 134217728'
sudo sysctl -w net.ipv4.tcp_wmem='4096 65536 134217728'
```

### Disable Power Saving

Ensure CPU is in performance mode, not power-saving.

## Verification

After installation, verify everything works:

```bash
# 1. Check Python version
python --version  # Should be 3.10+

# 2. Check dependencies
pip list | grep -E "MetaTrader5|numpy|pandas|torch"

# 3. Test MT5 connection
python -m trading_system.tests.test_mt5_connection

# 4. Run minimal system test
python main.py --test-mode
```

## Next Steps

After successful installation:
1. Read [CONFIGURATION.md](CONFIGURATION.md) for detailed configuration
2. Review [STRATEGY.md](STRATEGY.md) to understand the trading logic
3. Run backtests to validate system performance
4. Start with paper trading mode
5. Monitor system for at least 1 week before live trading

## Support

If you encounter issues not covered here:
1. Check the GitHub Issues page
2. Review the FAQ section
3. Open a new issue with detailed error logs

---

**Important**: Never run with `PAPER_TRADING=false` until you have thoroughly tested the system and understand all risks involved.
