"""Strategy loader from registry."""
import itertools
from typing import List, Dict, Any
from strategies.base import Strategy

# Import all strategy classes
from strategies.trend import (
    SMA_Crossover, EMA_Crossover, MACD_Cross, ADX_Trend,
    Supertrend, Parabolic_SAR, Price_Above_MA
)
from strategies.mean_reversion import (
    RSI_MeanReversion, RSI_2_Period, Bollinger_MeanReversion,
    Stochastic_MeanReversion, CCI_MeanReversion, Williams_R,
    ZScore_MeanReversion, RSI_With_MA_Filter
)
from strategies.momentum import (
    ROC_Momentum, Price_Momentum, MACD_Momentum,
    TSI_Momentum, Awesome_Oscillator, RSI_Momentum
)
from strategies.volatility import (
    ATR_Breakout, Volatility_Squeeze, RVI_Signal, ATR_Trailing_Stop
)
from strategies.volume import (
    OBV_Trend, VWAP_Cross, MFI_Signal, Volume_Spike, Force_Index
)
from strategies.pattern import (
    Rolling_High_Breakout, Inside_Bar_Breakout,
    Engulfing_Bullish, Hammer_Long
)
from strategies.seasonality import (
    DayOfWeek, TurnOfMonth, MonthOfYear, SellInMay, FirstFiveDays
)
from strategies.baselines import (
    BuyAndHold, Random_LongShort, Inverse_Best_Proxy
)

STRATEGY_MAP = {
    "SMA_Crossover": SMA_Crossover,
    "EMA_Crossover": EMA_Crossover,
    "MACD_Cross": MACD_Cross,
    "ADX_Trend": ADX_Trend,
    "Supertrend": Supertrend,
    "Parabolic_SAR": Parabolic_SAR,
    "Price_Above_MA": Price_Above_MA,
    "RSI_MeanReversion": RSI_MeanReversion,
    "RSI_2_Period": RSI_2_Period,
    "Bollinger_MeanReversion": Bollinger_MeanReversion,
    "Stochastic_MeanReversion": Stochastic_MeanReversion,
    "CCI_MeanReversion": CCI_MeanReversion,
    "Williams_R": Williams_R,
    "ZScore_MeanReversion": ZScore_MeanReversion,
    "RSI_With_MA_Filter": RSI_With_MA_Filter,
    "ROC_Momentum": ROC_Momentum,
    "Price_Momentum": Price_Momentum,
    "MACD_Momentum": MACD_Momentum,
    "TSI_Momentum": TSI_Momentum,
    "Awesome_Oscillator": Awesome_Oscillator,
    "RSI_Momentum": RSI_Momentum,
    "ATR_Breakout": ATR_Breakout,
    "Volatility_Squeeze": Volatility_Squeeze,
    "RVI_Signal": RVI_Signal,
    "ATR_Trailing_Stop": ATR_Trailing_Stop,
    "OBV_Trend": OBV_Trend,
    "VWAP_Cross": VWAP_Cross,
    "MFI_Signal": MFI_Signal,
    "Volume_Spike": Volume_Spike,
    "Force_Index": Force_Index,
    "Rolling_High_Breakout": Rolling_High_Breakout,
    "Inside_Bar_Breakout": Inside_Bar_Breakout,
    "Engulfing_Bullish": Engulfing_Bullish,
    "Hammer_Long": Hammer_Long,
    "DayOfWeek": DayOfWeek,
    "TurnOfMonth": TurnOfMonth,
    "MonthOfYear": MonthOfYear,
    "SellInMay": SellInMay,
    "FirstFiveDays": FirstFiveDays,
    "BuyAndHold": BuyAndHold,
    "Random_LongShort": Random_LongShort,
    "Inverse_Best_Proxy": Inverse_Best_Proxy,
}


def expand_param_grid(param_grid: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    """Expand a param grid into list of dicts."""
    keys = list(param_grid.keys())
    values = list(param_grid.values())
    return [dict(zip(keys, combo)) for combo in itertools.product(*values)]


def load_all_strategies(registry: Dict[str, List[Any]]) -> List[Strategy]:
    """Instantiate all strategy variants from registry."""
    strategies = []
    for category, items in registry.items():
        for class_name, param_grid in items:
            if class_name not in STRATEGY_MAP:
                continue
            cls = STRATEGY_MAP[class_name]
            if not param_grid:
                strategies.append(cls(class_name, {}))
            else:
                for params in expand_param_grid(param_grid):
                    # Skip invalid combos (e.g., fast >= slow)
                    if "fast" in params and "slow" in params and params["fast"] >= params["slow"]:
                        continue
                    strategies.append(cls(class_name, params))
    return strategies
