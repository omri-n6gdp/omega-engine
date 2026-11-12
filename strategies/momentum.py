"""Momentum strategies."""
import pandas as pd
import numpy as np
from strategies.base import Strategy


class ROC_Momentum(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        roc = df["close"].pct_change(period)
        df["signal"] = np.where(roc > 0, 1, -1)
        df["signal"] = df["signal"].where(roc.notna(), 0)
        return df


class Price_Momentum(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        df["signal"] = np.where(df["close"] > df["close"].shift(period), 1, -1)
        df["signal"] = df["signal"].where(df["close"].shift(period).notna(), 0)
        return df


class MACD_Momentum(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        fast = self.params["fast"]
        slow = self.params["slow"]
        signal = self.params["signal"]
        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        df["signal"] = np.where(macd > 0, 1, -1)
        df["signal"] = df["signal"].where(macd.notna(), 0)
        return df


class TSI_Momentum(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        r = self.params["r"]
        s = self.params["s"]
        pc = df["close"].diff()
        abs_pc = pc.abs()
        smooth_pc = pc.ewm(span=r, adjust=False).mean().ewm(span=s, adjust=False).mean()
        smooth_abs = abs_pc.ewm(span=r, adjust=False).mean().ewm(span=s, adjust=False).mean()
        tsi = 100 * smooth_pc / smooth_abs
        df["signal"] = np.where(tsi > 0, 1, -1)
        df["signal"] = df["signal"].where(tsi.notna(), 0)
        return df


class Awesome_Oscillator(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        fast = self.params["fast"]
        slow = self.params["slow"]
        median = (df["high"] + df["low"]) / 2
        ao = median.rolling(fast).mean() - median.rolling(slow).mean()
        df["signal"] = np.where(ao > 0, 1, -1)
        df["signal"] = df["signal"].where(ao.notna(), 0)
        return df


class RSI_Momentum(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        threshold = self.params["threshold"]
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        df["signal"] = np.where(rsi > threshold, 1, -1)
        df["signal"] = df["signal"].where(rsi.notna(), 0)
        return df
