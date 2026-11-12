#!/usr/bin/env python3
"""Omega Strategy Engine CLI."""
import argparse
import sys
import os
import time
from datetime import datetime
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DB_PATH, TICKERS, TIMEFRAMES, RISK_FREE_RATE, SLIPPAGE_PCT, COMMISSION_PER_SHARE, WALK_FORWARD_TRAIN_PCT
from data.database import DatabaseManager, BacktestResult
from data.fetcher import DataFetcher
from backtest.engine import run_backtest, run_walk_forward
from utils.loader import load_all_strategies, STRATEGY_MAP
from config import STRATEGY_REGISTRY


def cmd_fetch(args):
    db = DatabaseManager(DB_PATH)
    fetcher = DataFetcher(db, delay=0.3)
    for tf in TIMEFRAMES:
        print(f"\n=== Fetching {tf} ===")
        for ticker in tqdm(TICKERS, desc=tf):
            fetcher.fetch(ticker, tf, period="5y")


def cmd_backtest(args):
    db = DatabaseManager(DB_PATH)
    strategies = load_all_strategies(STRATEGY_REGISTRY)
    print(f"Loaded {len(strategies)} strategy variants")

    tickers = [args.ticker] if args.ticker else TICKERS
    timeframes = [args.timeframe] if args.timeframe else TIMEFRAMES

    total = len(strategies) * len(tickers) * len(timeframes)
    pbar = tqdm(total=total, desc="Backtesting")

    for strategy in strategies:
        for ticker in tickers:
            for tf in timeframes:
                pbar.update(1)

                # Skip if already exists
                if not args.force and db.result_exists(strategy.name, ticker, tf, strategy.param_key(), args.oos):
                    continue

                df = db.get_price_data(ticker, tf)
                if df.empty or len(df) < 100:
                    continue

                if args.walk_forward:
                    train_m, test_m = run_walk_forward(df, strategy, WALK_FORWARD_TRAIN_PCT, 
                                                        COMMISSION_PER_SHARE, SLIPPAGE_PCT, RISK_FREE_RATE)
                    # Save IS
                    if args.force or not db.result_exists(strategy.name, ticker, tf, strategy.param_key(), False):
                        _save_metrics(db, strategy, ticker, tf, train_m, False, df)
                    # Save OOS
                    if args.force or not db.result_exists(strategy.name, ticker, tf, strategy.param_key(), True):
                        _save_metrics(db, strategy, ticker, tf, test_m, True, df)
                else:
                    _, trades, metrics = run_backtest(df, strategy, COMMISSION_PER_SHARE, SLIPPAGE_PCT, RISK_FREE_RATE)
                    _save_metrics(db, strategy, ticker, tf, metrics, args.oos, df, trades)
    pbar.close()
    print("\n✓ Backtests complete")


def _save_metrics(db, strategy, ticker, tf, metrics, is_oos, df, trades=None):
    equity = (1 + df["close"].pct_change().fillna(0)).cumprod()
    equity_json = equity.to_json()
    trades_json = trades.to_json() if trades is not None and not trades.empty else "[]"

    result = BacktestResult(
        strategy_name=strategy.name,
        ticker=ticker,
        timeframe=tf,
        params=strategy.param_key(),
        is_oos=is_oos,
        start_date=str(df.index[0]),
        end_date=str(df.index[-1]),
        total_return=metrics.get("total_return", 0),
        annualized_return=metrics.get("annualized_return", 0),
        volatility=metrics.get("volatility", 0),
        sharpe_ratio=metrics.get("sharpe_ratio", 0),
        sortino_ratio=metrics.get("sortino_ratio", 0),
        max_drawdown=metrics.get("max_drawdown", 0),
        calmar_ratio=metrics.get("calmar_ratio", 0),
        win_rate=metrics.get("win_rate", 0),
        num_trades=metrics.get("num_trades", 0),
        avg_trade_return=metrics.get("avg_trade_return", 0),
        avg_win=metrics.get("avg_win", 0),
        avg_loss=metrics.get("avg_loss", 0),
        profit_factor=metrics.get("profit_factor", 0),
        expectancy=metrics.get("expectancy", 0),
        equity_curve=equity_json,
        trade_log=trades_json,
        created_at=datetime.now().isoformat()
    )
    db.save_backtest_result(result)


def cmd_dashboard(args):
    import subprocess
    port = args.port
    path = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")
    subprocess.run(["streamlit", "run", path, "--server.port", str(port)])


def cmd_status(args):
    db = DatabaseManager(DB_PATH)
    status = db.get_data_status()
    print(f"Tickers cached: {len(status)}")
    print(f"Total bars: {status['bars_count'].sum() if not status.empty else 0}")

    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM backtest_results")
    count = cursor.fetchone()[0]
    conn.close()
    print(f"Backtest results: {count}")


def cmd_daemon(args):
    print("Starting daemon loop (Ctrl+C to stop)...")
    while True:
        print(f"\n[{datetime.now()}] Running fetch + backtest...")
        cmd_fetch(argparse.Namespace())
        cmd_backtest(argparse.Namespace(ticker=None, timeframe=None, oos=False, walk_forward=True, force=False))
        print(f"Sleeping {args.interval} seconds...")
        time.sleep(args.interval)


def main():
    parser = argparse.ArgumentParser(description="Omega Strategy Engine")
    sub = parser.add_subparsers(dest="command")

    p_fetch = sub.add_parser("fetch", help="Download price data")

    p_bt = sub.add_parser("backtest", help="Run backtests")
    p_bt.add_argument("--ticker", default=None)
    p_bt.add_argument("--timeframe", default=None)
    p_bt.add_argument("--oos", action="store_true", help="Mark as OOS")
    p_bt.add_argument("--walk-forward", action="store_true", help="Run walk-forward split")
    p_bt.add_argument("--force", action="store_true", help="Overwrite existing")

    p_dash = sub.add_parser("dashboard", help="Launch Streamlit")
    p_dash.add_argument("--port", type=int, default=8501)

    p_status = sub.add_parser("status", help="Show database stats")

    p_daemon = sub.add_parser("daemon", help="Run forever")
    p_daemon.add_argument("--interval", type=int, default=21600, help="Seconds between cycles")

    args = parser.parse_args()

    if args.command == "fetch":
        cmd_fetch(args)
    elif args.command == "backtest":
        cmd_backtest(args)
    elif args.command == "dashboard":
        cmd_dashboard(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "daemon":
        cmd_daemon(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
