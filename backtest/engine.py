"""Vectorized backtest engine with walk-forward support."""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
from strategies.base import Strategy
from backtest.metrics import calculate_metrics


def run_backtest(df: pd.DataFrame, strategy: Strategy,
                 commission: float = 0.0,
                 slippage: float = 0.0005,
                 risk_free: float = 0.045) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Run a single vectorized backtest.
    Returns: (results_df, trades_df, metrics_dict)
    """
    if df.empty or len(df) < 50:
        return pd.DataFrame(), pd.DataFrame(), calculate_metrics(pd.Series(), pd.Series(), pd.DataFrame())

    # Generate signals (no lookahead guaranteed by strategy design)
    sig_df = strategy.generate_signals(df)
    df = df.copy()
    df["signal"] = sig_df["signal"]

    # Execute on next bar's open (realistic)
    df["position"] = df["signal"].shift(1).fillna(0)

    # Calculate market returns using next bar close vs current close
    # Actually, if we enter at next open, return should be based on close-to-close while holding
    df["market_return"] = df["close"].pct_change()
    df["strategy_return"] = df["position"].shift(1) * df["market_return"]

    # Costs on position change
    df["position_change"] = df["position"].diff().abs()
    df["costs"] = df["position_change"] * slippage
    df["strategy_return"] = df["strategy_return"] - df["costs"]

    # Equity curve
    df["equity"] = (1 + df["strategy_return"].fillna(0)).cumprod()

    # Extract trades
    trades = _extract_trades(df)

    # Metrics
    metrics = calculate_metrics(df["strategy_return"].fillna(0), df["equity"], trades, risk_free)

    return df, trades, metrics


def run_walk_forward(df: pd.DataFrame, strategy: Strategy,
                     train_pct: float = 0.70,
                     commission: float = 0.0,
                     slippage: float = 0.0005,
                     risk_free: float = 0.045) -> Tuple[Dict, Dict]:
    """Run in-sample and out-of-sample backtests."""
    split_idx = int(len(df) * train_pct)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    _, _, train_metrics = run_backtest(train_df, strategy, commission, slippage, risk_free)
    _, _, test_metrics = run_backtest(test_df, strategy, commission, slippage, risk_free)

    return train_metrics, test_metrics


def _extract_trades(df: pd.DataFrame) -> pd.DataFrame:
    """Extract individual trades from position series."""
    trades = []
    entry_date = None
    entry_price = None
    position = 0

    for i, row in df.iterrows():
        if pd.isna(row["position"]):
            continue
        if row["position"] != position and position == 0:
            # Entry
            entry_date = i
            entry_price = row["close"]
            position = row["position"]
        elif row["position"] != position and position != 0:
            # Exit
            if entry_price is not None:
                pnl = (row["close"] - entry_price) / entry_price * position
                trades.append({
                    "entry_date": entry_date,
                    "exit_date": i,
                    "position": position,
                    "entry_price": entry_price,
                    "exit_price": row["close"],
                    "pnl": pnl
                })
            if row["position"] != 0:
                entry_date = i
                entry_price = row["close"]
                position = row["position"]
            else:
                position = 0
                entry_date = None
                entry_price = None

    return pd.DataFrame(trades)
