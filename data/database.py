"""SQLite database manager with WAL mode for concurrent access."""
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import json
import os


@dataclass
class BacktestResult:
    strategy_name: str
    ticker: str
    timeframe: str
    params: str
    is_oos: bool
    start_date: str
    end_date: str
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    win_rate: float
    num_trades: int
    avg_trade_return: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    expectancy: float
    equity_curve: str
    trade_log: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DatabaseManager:
    """Manages SQLite DB for price data and backtest results."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def init_db(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_data (
                ticker TEXT,
                timeframe TEXT,
                date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                PRIMARY KEY (ticker, timeframe, date)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT,
                ticker TEXT,
                timeframe TEXT,
                params TEXT,
                is_oos INTEGER,
                start_date TEXT,
                end_date TEXT,
                total_return REAL,
                annualized_return REAL,
                volatility REAL,
                sharpe_ratio REAL,
                sortino_ratio REAL,
                max_drawdown REAL,
                calmar_ratio REAL,
                win_rate REAL,
                num_trades INTEGER,
                avg_trade_return REAL,
                avg_win REAL,
                avg_loss REAL,
                profit_factor REAL,
                expectancy REAL,
                equity_curve TEXT,
                trade_log TEXT,
                created_at TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_results_lookup 
            ON backtest_results(strategy_name, ticker, timeframe, params, is_oos)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_results_sharpe 
            ON backtest_results(sharpe_ratio)
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_status (
                ticker TEXT,
                timeframe TEXT,
                last_fetch TEXT,
                bars_count INTEGER,
                PRIMARY KEY (ticker, timeframe)
            )
        """)

        conn.commit()
        conn.close()

    def save_price_data(self, df: pd.DataFrame, ticker: str, timeframe: str):
        if df.empty:
            return
        conn = self._connect()
        df = df.copy()
        df = df.reset_index()
        date_col = "Date" if "Date" in df.columns else "Datetime"
        df = df.rename(columns={date_col: "date"})
        df["date"] = pd.to_datetime(df["date"]).astype(str)
        df["ticker"] = ticker
        df["timeframe"] = timeframe
        df = df[["ticker", "timeframe", "date", "Open", "High", "Low", "Close", "Volume"]]
        df.columns = ["ticker", "timeframe", "date", "open", "high", "low", "close", "volume"]

        df.to_sql("price_data", conn, if_exists="append", index=False, method="multi")
        conn.execute("DELETE FROM data_status WHERE ticker=? AND timeframe=?", (ticker, timeframe))
        conn.execute(
            "INSERT INTO data_status (ticker, timeframe, last_fetch, bars_count) VALUES (?, ?, ?, ?)",
            (ticker, timeframe, datetime.now().isoformat(), len(df))
        )
        conn.commit()
        conn.close()

    def get_price_data(self, ticker: str, timeframe: str,
                       start: Optional[str] = None,
                       end: Optional[str] = None) -> pd.DataFrame:
        conn = self._connect()
        query = "SELECT * FROM price_data WHERE ticker=? AND timeframe=?"
        params: List[Any] = [ticker, timeframe]
        if start:
            query += " AND date >= ?"
            params.append(start)
        if end:
            query += " AND date <= ?"
            params.append(end)
        query += " ORDER BY date"
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        if df.empty:
            return pd.DataFrame()
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        return df[["open", "high", "low", "close", "volume"]]

    def result_exists(self, strategy_name: str, ticker: str, timeframe: str,
                      params: str, is_oos: bool) -> bool:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM backtest_results WHERE strategy_name=? AND ticker=? AND timeframe=? AND params=? AND is_oos=? LIMIT 1",
            (strategy_name, ticker, timeframe, params, int(is_oos))
        )
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def save_backtest_result(self, result: BacktestResult):
        conn = self._connect()
        df = pd.DataFrame([result.to_dict()])
        df.to_sql("backtest_results", conn, if_exists="append", index=False)
        conn.close()

    def get_results(self, strategy_name: Optional[str] = None,
                    ticker: Optional[str] = None,
                    timeframe: Optional[str] = None,
                    is_oos: Optional[bool] = None,
                    min_sharpe: Optional[float] = None,
                    limit: int = 1000) -> pd.DataFrame:
        conn = self._connect()
        query = "SELECT * FROM backtest_results WHERE 1=1"
        params: List[Any] = []
        if strategy_name:
            query += " AND strategy_name=?"
            params.append(strategy_name)
        if ticker:
            query += " AND ticker=?"
            params.append(ticker)
        if timeframe:
            query += " AND timeframe=?"
            params.append(timeframe)
        if is_oos is not None:
            query += " AND is_oos=?"
            params.append(int(is_oos))
        if min_sharpe is not None:
            query += " AND sharpe_ratio >= ?"
            params.append(min_sharpe)
        query += " ORDER BY sharpe_ratio DESC LIMIT ?"
        params.append(limit)
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return df

    def get_data_status(self) -> pd.DataFrame:
        conn = self._connect()
        df = pd.read_sql("SELECT * FROM data_status", conn)
        conn.close()
        return df
