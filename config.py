"""Central configuration for the Omega Strategy Engine."""
import os
from typing import Dict, List, Any, Tuple

# Paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "engine.db")

# Universe
TICKERS: List[str] = [
    "SPY", "QQQ", "IWM", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META",
    "JPM", "V", "JNJ", "WMT", "UNH", "PG", "HD", "MA", "BAC", "ABBV",
    "PFE", "KO", "PEP", "COST", "TMO", "AVGO", "DIS", "CSCO", "VZ", "ADBE",
    "CRM", "ACN", "WFC", "MRK", "NKE", "ABT", "CMCSA", "XOM", "CVX", "TXN"
]

TIMEFRAMES: List[str] = ["1d", "1wk", "1mo"]

# Backtest defaults
RISK_FREE_RATE: float = 0.045
COMMISSION_PER_SHARE: float = 0.0
SLIPPAGE_PCT: float = 0.0005

# Walk-forward
WALK_FORWARD_TRAIN_PCT: float = 0.70

# Fetcher
FETCH_DELAY: float = 0.3
MAX_RETRIES: int = 3

# Strategy registry: category -> list of (class_name, param_grid_dict)
# Each param_grid_dict key -> list of values to grid-search
STRATEGY_REGISTRY: Dict[str, List[Tuple[str, Dict[str, List[Any]]]]] = {
    "trend": [
        ("SMA_Crossover", {"fast": [5, 10, 20, 50], "slow": [10, 20, 50, 200]}),
        ("EMA_Crossover", {"fast": [5, 10, 12, 20, 50], "slow": [10, 20, 26, 50, 200]}),
        ("MACD_Cross", {"fast": [12, 5, 8], "slow": [26, 35, 17], "signal": [9, 5, 9]}),
        ("ADX_Trend", {"period": [14, 20], "threshold": [20, 25, 30]}),
        ("Supertrend", {"period": [10, 14], "multiplier": [2.0, 3.0, 4.0]}),
        ("Parabolic_SAR", {"step": [0.02], "max": [0.2]}),
        ("Price_Above_MA", {"period": [20, 50, 100, 200], "ma_type": ["sma", "ema"]}),
    ],
    "mean_reversion": [
        ("RSI_MeanReversion", {"period": [7, 14, 21], "oversold": [20, 30], "overbought": [70, 80]}),
        ("RSI_2_Period", {"oversold": [5, 10], "overbought": [90, 95]}),
        ("Bollinger_MeanReversion", {"period": [20, 50], "std": [1.5, 2.0, 2.5]}),
        ("Stochastic_MeanReversion", {"k": [14, 10], "d": [3], "smooth": [3]}),
        ("CCI_MeanReversion", {"period": [14, 20], "threshold": [100, 200]}),
        ("Williams_R", {"period": [14, 10], "threshold": [20, 10]}),
        ("ZScore_MeanReversion", {"period": [20, 50, 100], "threshold": [1.5, 2.0, 2.5]}),
        ("RSI_With_MA_Filter", {"rsi_period": [2, 14], "ma_period": [200], "oversold": [10, 30], "overbought": [70, 90]}),
    ],
    "momentum": [
        ("ROC_Momentum", {"period": [10, 20, 60, 126]}),
        ("Price_Momentum", {"period": [20, 60, 126, 252]}),
        ("MACD_Momentum", {"fast": [12], "slow": [26], "signal": [9]}),
        ("TSI_Momentum", {"r": [25, 13], "s": [13, 7]}),
        ("Awesome_Oscillator", {"fast": [5], "slow": [34]}),
        ("RSI_Momentum", {"period": [14], "threshold": [50]}),
    ],
    "volatility": [
        ("ATR_Breakout", {"period": [14, 20], "multiplier": [1.5, 2.0]}),
        ("Volatility_Squeeze", {"bb_period": [20], "kc_period": [20], "bb_mult": [2.0], "kc_mult": [1.5]}),
        ("RVI_Signal", {"period": [14, 10]}),
        ("ATR_Trailing_Stop", {"period": [14], "multiplier": [2.0, 3.0]}),
    ],
    "volume": [
        ("OBV_Trend", {}),
        ("VWAP_Cross", {}),
        ("MFI_Signal", {"period": [14], "oversold": [20], "overbought": [80]}),
        ("Volume_Spike", {"period": [20], "mult": [2.0, 3.0]}),
        ("Force_Index", {"period": [13, 2]}),
    ],
    "pattern": [
        ("Rolling_High_Breakout", {"period": [20, 55, 100]}),
        ("Inside_Bar_Breakout", {}),
        ("Engulfing_Bullish", {}),
        ("Hammer_Long", {}),
    ],
    "seasonality": [
        ("DayOfWeek", {"day": [0, 1, 2, 3, 4]}),
        ("TurnOfMonth", {"days_before": [1], "days_after": [3]}),
        ("MonthOfYear", {"month": list(range(1, 13))}),
        ("SellInMay", {}),
        ("FirstFiveDays", {}),
    ],
    "baselines": [
        ("BuyAndHold", {}),
        ("Random_LongShort", {}),
        ("Inverse_Best_Proxy", {}),
    ]
}
