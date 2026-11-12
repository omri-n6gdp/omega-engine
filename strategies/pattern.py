"""Pattern-based strategies."""
import pandas as pd
import numpy as np
from strategies.base import Strategy


class Rolling_High_Breakout(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        highest = df["high"].rolling(period).max()
        lowest = df["low"].rolling(period).min()
        df["signal"] = np.where(df["close"] > highest.shift(1), 1,
                               np.where(df["close"] < lowest.shift(1), -1, 0))
        df["signal"] = df["signal"].where(highest.notna(), 0)
        return df


class Inside_Bar_Breakout(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        inside = (df["high"] < df["high"].shift(1)) & (df["low"] > df["low"].shift(1))
        df["signal"] = 0
        for i in range(1, len(df)):
            if inside.iloc[i-1]:
                if df["close"].iloc[i] > df["high"].iloc[i-1]:
                    df["signal"].iloc[i] = 1
                elif df["close"].iloc[i] < df["low"].iloc[i-1]:
                    df["signal"].iloc[i] = -1
        return df


class Engulfing_Bullish(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        prev_red = df["close"].shift(1) < df["open"].shift(1)
        curr_green = df["close"] > df["open"]
        engulf = (df["close"] > df["open"].shift(1)) & (df["open"] < df["close"].shift(1))
        df["signal"] = np.where(prev_red & curr_green & engulf, 1, 0)
        return df


class Hammer_Long(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        body = (df["close"] - df["open"]).abs()
        lower_shadow = np.where(df["close"] > df["open"],
                                df["open"] - df["low"],
                                df["close"] - df["low"])
        hammer = (lower_shadow > 2 * body) & (body > 0)
        df["signal"] = np.where(hammer, 1, 0)
        return df
