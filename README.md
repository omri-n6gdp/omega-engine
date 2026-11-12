# 🔥 Omega Strategy Engine

A research-grade, local, free trading strategy backtesting platform that tests hundreds of strategy variants across multiple timeframes with walk-forward analysis and anti-overfitting measures.

## ⚠️ Disclaimer
This is for **educational and research purposes only**. Past performance does not guarantee future results. No strategy here is investment advice.

## 🚀 Quick Start

```bash
# 1. Clone/navigate to the project
cd omega_engine

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download price data (cached locally in SQLite)
python main.py fetch

# 4. Run backtests (this takes a while for full run)
python main.py backtest

# 5. Launch dashboard
python main.py dashboard
```

Then open http://localhost:8501 in your browser.

## 📁 Project Structure

```
omega_engine/
├── data/
│   ├── database.py      # SQLite manager (WAL mode)
│   └── fetcher.py       # Yahoo Finance wrapper with caching
├── strategies/
│   ├── base.py          # Abstract base class
│   ├── trend.py         # MA crossovers, MACD, ADX, Supertrend, Parabolic SAR
│   ├── mean_reversion.py # RSI, Bollinger, Stochastic, CCI, Williams %R, Z-Score
│   ├── momentum.py      # ROC, Price momentum, TSI, Awesome Oscillator
│   ├── volatility.py    # ATR breakout, Volatility Squeeze, RVI
│   ├── volume.py        # OBV, VWAP, MFI, Volume Spike, Force Index
│   ├── pattern.py       # Breakouts, Inside Bar, Engulfing, Hammer
│   ├── seasonality.py   # Day-of-week, Turn-of-month, Sell in May
│   └── baselines.py     # Buy & Hold, Random, Inverse
├── backtest/
│   ├── engine.py        # Vectorized backtester + walk-forward
│   └── metrics.py       # Sharpe, Sortino, Calmar, Profit Factor, etc.
├── dashboard/
│   └── app.py           # Streamlit dashboard
├── utils/
│   └── loader.py        # Strategy registry & instantiation
├── config.py            # Tickers, timeframes, parameter grids
└── main.py              # CLI entry point
```

## 🧪 What's Included

### Strategies (40+ classes, 200+ parameter variants)
- **Trend:** SMA/EMA/DEMA/TEMA/HMA/KAMA crossovers, MACD, ADX, Supertrend, Parabolic SAR, Ichimoku proxies
- **Mean Reversion:** RSI (classic, 2-period, with MA filter), Bollinger Bands, Stochastic, CCI, Williams %R, Z-Score
- **Momentum:** ROC, Price momentum, TSI, Awesome Oscillator, Coppock proxy, KST
- **Volatility:** ATR breakout, Volatility Squeeze, RVI, ATR trailing stop
- **Volume:** OBV, VWAP, MFI, Volume spikes, Force Index
- **Pattern:** Rolling high/low breakouts, Inside Bar, Engulfing, Hammer
- **Seasonality:** Day-of-week, Turn-of-month, Month-of-year, Sell in May, First Five Days
- **Baselines:** Buy & Hold, Random Long/Short, Inverse

### Backtest Features
- **Vectorized execution:** Fast pandas/numpy backtesting
- **Realistic execution:** Signals generated at bar close, executed next bar open
- **Cost modeling:** Configurable slippage (default 0.05%) and commission
- **Walk-forward analysis:** Train/test split to detect overfitting
- **Comprehensive metrics:** Sharpe, Sortino, Calmar, Max Drawdown, Win Rate, Profit Factor, Expectancy

### Dashboard
- **Leaderboard:** Rank strategies by Sharpe, filter by ticker/timeframe
- **Strategy Autopsy:** Equity curves, drawdowns, parameter inspection
- **Overfitting Report:** IS vs OOS scatter plot, survivor count
- **Data Health:** Cache status, bar counts, staleness

## 🖥️ CLI Commands

```bash
# Download/update price data
python main.py fetch

# Run all backtests
python main.py backtest

# Run with walk-forward (IS + OOS)
python main.py backtest --walk-forward

# Backtest single ticker
python main.py backtest --ticker SPY

# Backtest single timeframe
python main.py backtest --timeframe 1d

# Force re-run existing
python main.py backtest --force

# Launch dashboard
python main.py dashboard

# Launch on different port
python main.py dashboard --port 8888

# Check database stats
python main.py status

# Run 24/7 daemon (fetch + backtest every 6 hours)
python main.py daemon --interval 21600
```

## 🌙 Running 24/7

### Linux/Mac:
```bash
nohup python main.py daemon > engine.log 2>&1 &
```

### Windows (PowerShell):
```powershell
Start-Process python -ArgumentList "main.py daemon" -WindowStyle Hidden -RedirectStandardOutput engine.log
```

### Systemd service (Linux):
Create `/etc/systemd/system/omega-engine.service`:
```ini
[Unit]
Description=Omega Strategy Engine
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/omega_engine
ExecStart=/usr/bin/python3 /path/to/omega_engine/main.py daemon
Restart=always

[Install]
WantedBy=multi-user.target
```

## ➕ Adding a New Strategy

1. Create a class in `strategies/your_category.py`:
```python
from strategies.base import Strategy
import pandas as pd
import numpy as np

class MyStrategy(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        # Your logic here (NO lookahead bias!)
        df["signal"] = np.where(df["close"] > df["close"].rolling(period).mean(), 1, -1)
        df["signal"] = df["signal"].where(df["close"].rolling(period).mean().notna(), 0)
        return df
```

2. Import it in `strategies/__init__.py`
3. Add to `STRATEGY_MAP` in `utils/loader.py`
4. Add parameter grid to `config.py`:
```python
("MyStrategy", {"period": [10, 20, 50]})
```
5. Run `python main.py backtest`

## 🔍 Interpreting Results

- **Sharpe > 1.0:** Good risk-adjusted returns
- **Sharpe > 0.5 AND OOS Sharpe > 0.5:** Potential survivor (not overfit)
- **Max DD > 50%:** Likely ruin in live trading
- **Profit Factor > 1.5:** Decent edge
- **Num Trades < 10:** Statistically meaningless
- **IS Sharpe >> OOS Sharpe:** Overfitting detected

## 🛠️ Tech Stack
- **Python 3.10+**
- **yfinance:** Free Yahoo Finance data
- **pandas/numpy:** Vectorized computation
- **SQLite:** Local database (WAL mode for concurrency)
- **Streamlit + Plotly:** Dashboard
- **tqdm:** Progress bars

## 📊 Performance Expectations
- Full run (40 tickers × ~200 strategies × 3 timeframes): **2–6 hours** on 8 cores
- Incremental runs: **Minutes** (skips existing results)
- Database size: **~500MB** after full run
- Memory usage: **< 2GB** (streams to disk)

## 🐛 Troubleshooting

**Yahoo rate limiting:**
- The fetcher has built-in delays (0.3s between requests)
- If blocked, wait 1 hour and retry

**Missing data for a ticker:**
- Some tickers delist or have gaps
- Engine skips gracefully with a warning

**Dashboard won't start:**
- Check port 8501 isn't in use: `lsof -i :8501`
- Try: `python main.py dashboard --port 8502`

**SQLite locked:**
- WAL mode handles most concurrency
- Close dashboard before running backtests if issues occur

## 📜 License
MIT — use at your own risk. Not financial advice.
