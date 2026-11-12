"""Volume-based strategies."""
import pandas as pd
import numpy as np
from strategies.base import Strategy


class OBV_Trend(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        obv = pd.Series(index=df.index, dtype=float)
        obv.iloc[0] = df["volume"].iloc[0]
        for i in range(1, len(df)):
            if df["close"].iloc[i] > df["close"].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + df["volume"].iloc[i]
            elif df["close"].iloc[i] < df["close"].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - df["volume"].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        obv_ma = obv.rolling(20).mean()
        df["signal"] = np.where(obv > obv_ma, 1, -1)
        df["signal"] = df["signal"].where(obv_ma.notna(), 0)
        return df


class VWAP_Cross(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        vwap = (df["close"] * df["volume"]).cumsum() / df["volume"].cumsum()
        df["signal"] = np.where(df["close"] > vwap, 1, -1)
        df["signal"] = df["signal"].where(vwap.notna(), 0)
        return df


class MFI_Signal(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        tp = (df["high"] + df["low"] + df["close"]) / 3
        rmf = tp * df["volume"]
        pos = pd.Series(np.where(tp > tp.shift(1), rmf, 0), index=df.index)
        neg = pd.Series(np.where(tp < tp.shift(1), rmf, 0), index=df.index)
        mfi = 100 - (100 / (1 + pos.rolling(period).sum() / neg.rolling(period).sum()))
        oversold = self.params["oversold"]
        overbought = self.params["overbought"]
        df["signal"] = np.where(mfi < oversold, 1, np.where(mfi > overbought, -1, 0))
        df["signal"] = df["signal"].where(mfi.notna(), 0)
        return df


class Volume_Spike(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        mult = self.params["mult"]
        vol_ma = df["volume"].rolling(period).mean()
        spike = df["volume"] > mult * vol_ma
        df["signal"] = np.where(spike & (df["close"] > df["open"]), 1,
                               np.where(spike & (df["close"] < df["open"]), -1, 0))
        df["signal"] = df["signal"].where(vol_ma.notna(), 0)
        return df


class Force_Index(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        fi = df["close"].diff() * df["volume"]
        fi_ema = fi.ewm(span=period, adjust=False).mean()
        df["signal"] = np.where(fi_ema > 0, 1, -1)
        df["signal"] = df["signal"].where(fi_ema.notna(), 0)
        return df
