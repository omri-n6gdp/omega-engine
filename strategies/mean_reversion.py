"""Mean-reversion strategies."""
import pandas as pd
import numpy as np
from strategies.base import Strategy


class RSI_MeanReversion(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        oversold = self.params["oversold"]
        overbought = self.params["overbought"]
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        df["signal"] = np.where(rsi < oversold, 1, np.where(rsi > overbought, -1, 0))
        df["signal"] = df["signal"].where(rsi.notna(), 0)
        return df


class RSI_2_Period(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        oversold = self.params["oversold"]
        overbought = self.params["overbought"]
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(2).mean()
        avg_loss = loss.rolling(2).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        df["signal"] = np.where(rsi < oversold, 1, np.where(rsi > overbought, -1, 0))
        df["signal"] = df["signal"].where(rsi.notna(), 0)
        return df


class Bollinger_MeanReversion(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        std = self.params["std"]
        ma = df["close"].rolling(period).mean()
        sigma = df["close"].rolling(period).std()
        upper = ma + std * sigma
        lower = ma - std * sigma
        df["signal"] = np.where(df["close"] < lower, 1, np.where(df["close"] > upper, -1, 0))
        df["signal"] = df["signal"].where(ma.notna(), 0)
        return df


class Stochastic_MeanReversion(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        k_period = self.params["k"]
        d_period = self.params["d"]
        smooth = self.params["smooth"]
        lowest = df["low"].rolling(k_period).min()
        highest = df["high"].rolling(k_period).max()
        k = 100 * (df["close"] - lowest) / (highest - lowest)
        d = k.rolling(d_period).mean()
        df["signal"] = np.where(d < 20, 1, np.where(d > 80, -1, 0))
        df["signal"] = df["signal"].where(d.notna(), 0)
        return df


class CCI_MeanReversion(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        threshold = self.params["threshold"]
        tp = (df["high"] + df["low"] + df["close"]) / 3
        ma = tp.rolling(period).mean()
        md = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        cci = (tp - ma) / (0.015 * md)
        df["signal"] = np.where(cci < -threshold, 1, np.where(cci > threshold, -1, 0))
        df["signal"] = df["signal"].where(ma.notna(), 0)
        return df


class Williams_R(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        threshold = self.params["threshold"]
        highest = df["high"].rolling(period).max()
        lowest = df["low"].rolling(period).min()
        wr = -100 * (highest - df["close"]) / (highest - lowest)
        df["signal"] = np.where(wr < -100 + threshold, 1, np.where(wr > -threshold, -1, 0))
        df["signal"] = df["signal"].where(highest.notna(), 0)
        return df


class ZScore_MeanReversion(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        threshold = self.params["threshold"]
        ma = df["close"].rolling(period).mean()
        sigma = df["close"].rolling(period).std()
        z = (df["close"] - ma) / sigma
        df["signal"] = np.where(z < -threshold, 1, np.where(z > threshold, -1, 0))
        df["signal"] = df["signal"].where(ma.notna(), 0)
        return df


class RSI_With_MA_Filter(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        rsi_p = self.params["rsi_period"]
        ma_p = self.params["ma_period"]
        oversold = self.params["oversold"]
        overbought = self.params["overbought"]
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(rsi_p).mean()
        avg_loss = loss.rolling(rsi_p).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        ma = df["close"].rolling(ma_p).mean()
        df["signal"] = np.where((rsi < oversold) & (df["close"] > ma), 1,
                               np.where((rsi > overbought) & (df["close"] < ma), -1, 0))
        df["signal"] = df["signal"].where(rsi.notna() & ma.notna(), 0)
        return df
