"""Performance metrics calculation."""
import numpy as np
import pandas as pd
from typing import Dict, Any


def calculate_metrics(returns: pd.Series, equity: pd.Series, 
                      trades: pd.DataFrame, risk_free: float = 0.045) -> Dict[str, float]:
    """Calculate comprehensive performance metrics."""
    returns = returns.dropna()
    if len(returns) == 0 or returns.std() == 0:
        return _empty_metrics()

    # Basic returns
    total_return = equity.iloc[-1] / equity.iloc[0] - 1 if equity.iloc[0] != 0 else 0
    n_years = len(returns) / 252
    ann_return = (1 + total_return) ** (1 / max(n_years, 1e-6)) - 1 if total_return > -1 else -1

    # Volatility
    vol = returns.std() * np.sqrt(252)

    # Sharpe
    sharpe = (ann_return - risk_free) / vol if vol != 0 else 0

    # Sortino
    downside = returns[returns < 0].std() * np.sqrt(252)
    sortino = (ann_return - risk_free) / downside if downside != 0 else 0

    # Drawdown
    peak = equity.cummax()
    dd = (equity - peak) / peak
    max_dd = dd.min()

    # Calmar
    calmar = ann_return / abs(max_dd) if max_dd != 0 else 0

    # Trade metrics
    if trades.empty:
        return {**{"total_return": total_return, "annualized_return": ann_return,
                   "volatility": vol, "sharpe_ratio": sharpe, "sortino_ratio": sortino,
                   "max_drawdown": max_dd, "calmar_ratio": calmar},
                **_empty_trade_metrics()}

    wins = trades[trades["pnl"] > 0]
    losses = trades[trades["pnl"] <= 0]
    num_trades = len(trades)
    win_rate = len(wins) / num_trades if num_trades > 0 else 0
    avg_trade = trades["pnl"].mean()
    avg_win = wins["pnl"].mean() if len(wins) > 0 else 0
    avg_loss = losses["pnl"].mean() if len(losses) > 0 else 0
    profit_factor = abs(wins["pnl"].sum() / losses["pnl"].sum()) if losses["pnl"].sum() != 0 else float("inf")
    expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss) if num_trades > 0 else 0

    return {
        "total_return": total_return,
        "annualized_return": ann_return,
        "volatility": vol,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "max_drawdown": max_dd,
        "calmar_ratio": calmar,
        "win_rate": win_rate,
        "num_trades": num_trades,
        "avg_trade_return": avg_trade,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "expectancy": expectancy,
    }


def _empty_metrics() -> Dict[str, float]:
    return {k: 0.0 for k in [
        "total_return", "annualized_return", "volatility", "sharpe_ratio",
        "sortino_ratio", "max_drawdown", "calmar_ratio"
    ]}


def _empty_trade_metrics() -> Dict[str, Any]:
    return {
        "win_rate": 0.0, "num_trades": 0, "avg_trade_return": 0.0,
        "avg_win": 0.0, "avg_loss": 0.0, "profit_factor": 0.0, "expectancy": 0.0
    }
