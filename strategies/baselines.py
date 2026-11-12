"""Baseline and control strategies."""
import pandas as pd
import numpy as np
from strategies.base import Strategy


class BuyAndHold(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["signal"] = 1
        return df


class Random_LongShort(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        np.random.seed(42)
        df["signal"] = np.random.choice([-1, 1], size=len(df))
        return df


class Inverse_Best_Proxy(Strategy):
    """Placeholder: inverts the signal of whatever strategy is currently best.
    Actual inversion handled by engine meta-layer."""
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["signal"] = 0
        return df
