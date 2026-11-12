"""Volatility-based strategies."""
import pandas as pd
import numpy as np
from strategies.base import Strategy


class ATR_Breakout(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        mult = self.params["multiplier"]
        tr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - df["close"].shift(1)).abs(),
            (df["low"] - df["close"].shift(1)).abs()
        ], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        df["signal"] = np.where(tr > mult * atr, np.where(df["close"] > df["open"], 1, -1), 0)
        df["signal"] = df["signal"].where(atr.notna(), 0)
        return df


class Volatility_Squeeze(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        bb_p = self.params["bb_period"]
        kc_p = self.params["kc_period"]
        bb_m = self.params["bb_mult"]
        kc_m = self.params["kc_mult"]
        # Bollinger
        bb_ma = df["close"].rolling(bb_p).mean()
        bb_std = df["close"].rolling(bb_p).std()
        bb_upper = bb_ma + bb_m * bb_std
        bb_lower = bb_ma - bb_m * bb_std
        bb_width = bb_upper - bb_lower
        # Keltner
        tr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - df["close"].shift(1)).abs(),
            (df["low"] - df["close"].shift(1)).abs()
        ], axis=1).max(axis=1)
        atr = tr.rolling(kc_p).mean()
        kc_upper = bb_ma + kc_m * atr
        kc_lower = bb_ma - kc_m * atr
        kc_width = kc_upper - kc_lower
        squeeze = bb_width < kc_width
        # Trade breakout direction after squeeze
        df["signal"] = 0
        for i in range(1, len(df)):
            if squeeze.iloc[i-1] and not squeeze.iloc[i]:
                df["signal"].iloc[i] = 1 if df["close"].iloc[i] > df["close"].iloc[i-1] else -1
        return df


class RVI_Signal(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        std = df["close"].rolling(period).std()
        rvi = std.rolling(period).mean()  # Simplified RVI
        rvi_signal = rvi.rolling(period).mean()
        df["signal"] = np.where(rvi > rvi_signal, 1, -1)
        df["signal"] = df["signal"].where(rvi.notna(), 0)
        return df


class ATR_Trailing_Stop(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        mult = self.params["multiplier"]
        tr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - df["close"].shift(1)).abs(),
            (df["low"] - df["close"].shift(1)).abs()
        ], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        upper = df["close"] + mult * atr
        lower = df["close"] - mult * atr
        trend = pd.Series(1, index=df.index)
        for i in range(1, len(df)):
            if df["close"].iloc[i] > upper.iloc[i-1]:
                trend.iloc[i] = 1
            elif df["close"].iloc[i] < lower.iloc[i-1]:
                trend.iloc[i] = -1
            else:
                trend.iloc[i] = trend.iloc[i-1]
        df["signal"] = trend
        df["signal"] = df["signal"].where(atr.notna(), 0)
        return df
