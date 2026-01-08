# API Documentation

## REST API

The trading system provides a FastAPI-based REST API for monitoring and control.

### Base URL
```
http://localhost:8000
```

## Endpoints

### System Status

#### GET /status
Get current system status.

**Response**:
```json
{
  "status": "running",
  "uptime_seconds": 3600,
  "connected": true,
  "paper_trading": true,
  "version": "1.0.0"
}
```

#### GET /health
Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-08T14:00:00Z"
}
```

### Trading Control

#### POST /trading/start
Start trading.

**Request**:
```json
{
  "risk_mode": "moderate"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Trading started",
  "risk_mode": "moderate"
}
```

#### POST /trading/stop
Stop trading.

**Response**:
```json
{
  "success": true,
  "message": "Trading stopped"
}
```

#### POST /trading/emergency_close
Emergency close all positions.

**Response**:
```json
{
  "success": true,
  "positions_closed": 3,
  "message": "All positions closed"
}
```

### Positions

#### GET /positions
Get all open positions.

**Response**:
```json
{
  "positions": [
    {
      "ticket": 12345,
      "symbol": "XAUUSD",
      "side": "long",
      "volume": 0.01,
      "entry_price": 2000.50,
      "current_price": 2005.30,
      "profit": 4.80,
      "duration_seconds": 120
    }
  ],
  "count": 1,
  "total_profit": 4.80
}
```

#### GET /positions/{ticket}
Get specific position details.

**Response**:
```json
{
  "ticket": 12345,
  "symbol": "XAUUSD",
  "side": "long",
  "volume": 0.01,
  "entry_price": 2000.50,
  "current_price": 2005.30,
  "stop_loss": 1995.00,
  "take_profit": 2010.00,
  "profit": 4.80
}
```

### Trade History

#### GET /trades
Get trade history.

**Query Parameters**:
- `limit` (int): Maximum number of trades (default: 50)
- `start_time` (timestamp): Filter start time
- `end_time` (timestamp): Filter end time
- `symbol` (string): Filter by symbol

**Response**:
```json
{
  "trades": [
    {
      "id": 1,
      "timestamp": 1704729600.0,
      "symbol": "XAUUSD",
      "action": "buy",
      "volume": 0.01,
      "entry_price": 2000.00,
      "exit_price": 2005.00,
      "pnl": 5.00,
      "duration_seconds": 60
    }
  ],
  "count": 1
}
```

### Performance Metrics

#### GET /metrics
Get current performance metrics.

**Response**:
```json
{
  "equity": 10500.00,
  "balance": 10450.00,
  "daily_pnl": 500.00,
  "daily_pnl_percent": 5.0,
  "total_trades": 50,
  "winning_trades": 28,
  "losing_trades": 22,
  "win_rate": 0.56,
  "profit_factor": 1.8,
  "sharpe_ratio": 2.1,
  "max_drawdown": 3.5,
  "avg_latency_ms": 8.5
}
```

#### GET /metrics/history
Get performance history.

**Query Parameters**:
- `period` (string): "1h", "24h", "7d", "30d"

**Response**:
```json
{
  "timestamps": [1704729600, 1704730200, ...],
  "equity": [10000, 10050, ...],
  "pnl": [0, 50, ...],
  "drawdown": [0, 0.5, ...]
}
```

### Risk Management

#### GET /risk/summary
Get risk management summary.

**Response**:
```json
{
  "risk_mode": "moderate",
  "trading_enabled": true,
  "daily_pnl": 150.00,
  "max_drawdown": 2.5,
  "current_positions": 2,
  "max_positions": 3,
  "margin_level": 1000.0
}
```

#### POST /risk/mode
Change risk mode.

**Request**:
```json
{
  "mode": "conservative"
}
```

**Response**:
```json
{
  "success": true,
  "mode": "conservative",
  "message": "Risk mode updated"
}
```

### Market Data

#### GET /market/tick
Get latest tick data.

**Query Parameters**:
- `symbol` (string): Trading symbol (default: XAUUSD)

**Response**:
```json
{
  "timestamp": 1704729600.0,
  "symbol": "XAUUSD",
  "bid": 2000.50,
  "ask": 2000.70,
  "spread": 0.20,
  "mid_price": 2000.60
}
```

#### GET /market/microstructure
Get microstructure analysis.

**Response**:
```json
{
  "vpin": 0.45,
  "is_toxic_flow": false,
  "spread_regime": "normal",
  "entropy": 0.62,
  "order_imbalance": 0.15,
  "imbalance_strength": "weak_buy"
}
```

## WebSocket API

### Connection
```
ws://localhost:8001/ws
```

### Events

#### Subscribe
```json
{
  "action": "subscribe",
  "channels": ["ticks", "positions", "trades", "metrics"]
}
```

#### Tick Updates
```json
{
  "type": "tick",
  "data": {
    "timestamp": 1704729600.0,
    "symbol": "XAUUSD",
    "bid": 2000.50,
    "ask": 2000.70
  }
}
```

#### Position Updates
```json
{
  "type": "position_update",
  "data": {
    "ticket": 12345,
    "profit": 5.50,
    "current_price": 2005.50
  }
}
```

#### Trade Executed
```json
{
  "type": "trade",
  "data": {
    "action": "buy",
    "symbol": "XAUUSD",
    "volume": 0.01,
    "price": 2000.50,
    "ticket": 12345
  }
}
```

#### Metrics Update
```json
{
  "type": "metrics",
  "data": {
    "equity": 10550.00,
    "daily_pnl": 550.00,
    "open_positions": 2
  }
}
```

## Error Responses

All endpoints return standard error responses:

```json
{
  "error": true,
  "message": "Error description",
  "code": "ERROR_CODE"
}
```

### Error Codes
- `AUTH_REQUIRED`: Authentication required
- `INVALID_PARAMS`: Invalid parameters
- `NOT_FOUND`: Resource not found
- `SYSTEM_ERROR`: Internal system error
- `TRADING_DISABLED`: Trading is disabled
- `RISK_LIMIT_EXCEEDED`: Risk limit exceeded

## Rate Limiting

- **REST API**: 100 requests per minute per IP
- **WebSocket**: 1000 messages per minute per connection

## Authentication (Optional)

If authentication is enabled:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/status
```

## Examples

### Python Client

```python
import requests

base_url = "http://localhost:8000"

# Get system status
response = requests.get(f"{base_url}/status")
print(response.json())

# Get positions
response = requests.get(f"{base_url}/positions")
positions = response.json()['positions']

# Emergency close
response = requests.post(f"{base_url}/trading/emergency_close")
print(response.json())
```

### WebSocket Client

```python
import asyncio
import websockets
import json

async def listen():
    uri = "ws://localhost:8001/ws"
    async with websockets.connect(uri) as websocket:
        # Subscribe to channels
        await websocket.send(json.dumps({
            "action": "subscribe",
            "channels": ["ticks", "trades"]
        }))
        
        # Listen for messages
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data['type']}")

asyncio.run(listen())
```

### JavaScript Client

```javascript
// REST API
fetch('http://localhost:8000/positions')
  .then(response => response.json())
  .then(data => console.log(data));

// WebSocket
const ws = new WebSocket('ws://localhost:8001/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'subscribe',
    channels: ['ticks', 'trades']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

## Dashboard API Integration

The web dashboard uses both REST and WebSocket APIs:

- **Initial Load**: REST API for current state
- **Real-time Updates**: WebSocket for live data
- **Controls**: REST API for actions

---

**Note**: Full API implementation is in `dashboard/backend/api.py` and `dashboard/backend/websocket_server.py`
