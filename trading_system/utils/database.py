"""Database layer for data persistence."""
import sqlite3
import aiosqlite
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import json


class TradingDatabase:
    """SQLite database for trading data persistence."""
    
    def __init__(self, db_path: Path):
        """
        Initialize the database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[aiosqlite.Connection] = None
        
    async def connect(self) -> None:
        """Connect to the database and create tables."""
        self._conn = await aiosqlite.connect(str(self.db_path))
        await self._create_tables()
        
    async def close(self) -> None:
        """Close database connection."""
        if self._conn:
            await self._conn.close()
            
    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                volume REAL NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                stop_loss REAL,
                take_profit REAL,
                pnl REAL,
                commission REAL,
                duration_seconds REAL,
                signal_strength REAL,
                regime TEXT,
                metadata TEXT
            )
        """)
        
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                symbol TEXT NOT NULL,
                order_type TEXT NOT NULL,
                volume REAL NOT NULL,
                price REAL NOT NULL,
                status TEXT NOT NULL,
                execution_time_ms REAL,
                slippage REAL,
                metadata TEXT
            )
        """)
        
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                equity REAL NOT NULL,
                balance REAL NOT NULL,
                margin_used REAL,
                free_margin REAL,
                pnl_daily REAL,
                open_positions INTEGER,
                total_trades INTEGER,
                win_rate REAL,
                sharpe_ratio REAL,
                drawdown REAL,
                metadata TEXT
            )
        """)
        
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS tick_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                symbol TEXT NOT NULL,
                bid REAL NOT NULL,
                ask REAL NOT NULL,
                last REAL,
                volume REAL,
                metadata TEXT
            )
        """)
        
        # Create indices
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)")
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_timestamp ON orders(timestamp)")
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance(timestamp)")
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_tick_data_timestamp ON tick_data(timestamp)")
        
        await self._conn.commit()
        
    async def insert_trade(self, trade_data: Dict[str, Any]) -> int:
        """Insert a trade record."""
        cursor = await self._conn.execute("""
            INSERT INTO trades (
                timestamp, symbol, action, volume, entry_price, exit_price,
                stop_loss, take_profit, pnl, commission, duration_seconds,
                signal_strength, regime, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_data.get('timestamp', datetime.utcnow().timestamp()),
            trade_data['symbol'],
            trade_data['action'],
            trade_data['volume'],
            trade_data['entry_price'],
            trade_data.get('exit_price'),
            trade_data.get('stop_loss'),
            trade_data.get('take_profit'),
            trade_data.get('pnl'),
            trade_data.get('commission'),
            trade_data.get('duration_seconds'),
            trade_data.get('signal_strength'),
            trade_data.get('regime'),
            json.dumps(trade_data.get('metadata', {}))
        ))
        await self._conn.commit()
        return cursor.lastrowid
        
    async def insert_order(self, order_data: Dict[str, Any]) -> int:
        """Insert an order record."""
        cursor = await self._conn.execute("""
            INSERT INTO orders (
                timestamp, symbol, order_type, volume, price, status,
                execution_time_ms, slippage, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_data.get('timestamp', datetime.utcnow().timestamp()),
            order_data['symbol'],
            order_data['order_type'],
            order_data['volume'],
            order_data['price'],
            order_data['status'],
            order_data.get('execution_time_ms'),
            order_data.get('slippage'),
            json.dumps(order_data.get('metadata', {}))
        ))
        await self._conn.commit()
        return cursor.lastrowid
        
    async def insert_performance(self, perf_data: Dict[str, Any]) -> int:
        """Insert a performance snapshot."""
        cursor = await self._conn.execute("""
            INSERT INTO performance (
                timestamp, equity, balance, margin_used, free_margin,
                pnl_daily, open_positions, total_trades, win_rate,
                sharpe_ratio, drawdown, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            perf_data.get('timestamp', datetime.utcnow().timestamp()),
            perf_data['equity'],
            perf_data['balance'],
            perf_data.get('margin_used'),
            perf_data.get('free_margin'),
            perf_data.get('pnl_daily'),
            perf_data.get('open_positions'),
            perf_data.get('total_trades'),
            perf_data.get('win_rate'),
            perf_data.get('sharpe_ratio'),
            perf_data.get('drawdown'),
            json.dumps(perf_data.get('metadata', {}))
        ))
        await self._conn.commit()
        return cursor.lastrowid
        
    async def get_trades(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get trade records."""
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
            
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        async with self._conn.execute(query, params) as cursor:
            columns = [desc[0] for desc in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
            
    async def get_performance_history(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get performance history."""
        query = "SELECT * FROM performance WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
            
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        async with self._conn.execute(query, params) as cursor:
            columns = [desc[0] for desc in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
