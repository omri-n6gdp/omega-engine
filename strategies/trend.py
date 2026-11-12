"""Trend-following strategies."""
import pandas as pd
import numpy as np
from strategies.base import Strategy


class SMA_Crossover(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        fast = self.params["fast"]
        slow = self.params["slow"]
        if fast >= slow:
            df["signal"] = 0
            return df
        df["ma_fast"] = df["close"].rolling(fast).mean()
        df["ma_slow"] = df["close"].rolling(slow).mean()
        df["signal"] = np.where(df["ma_fast"] > df["ma_slow"], 1, -1)
        df["signal"] = df["signal"].where(df["ma_fast"].notna() & df["ma_slow"].notna(), 0)
        return df


class EMA_Crossover(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        fast = self.params["fast"]
        slow = self.params["slow"]
        if fast >= slow:
            df["signal"] = 0
            return df
        df["ema_fast"] = df["close"].ewm(span=fast, adjust=False).mean()
        df["ema_slow"] = df["close"].ewm(span=slow, adjust=False).mean()
        df["signal"] = np.where(df["ema_fast"] > df["ema_slow"], 1, -1)
        df["signal"] = df["signal"].where(df["ema_fast"].notna() & df["ema_slow"].notna(), 0)
        return df


class MACD_Cross(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        fast = self.params["fast"]
        slow = self.params["slow"]
        signal = self.params["signal"]
        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        df["signal"] = np.where(macd > macd_signal, 1, -1)
        df["signal"] = df["signal"].where(macd_signal.notna(), 0)
        return df


class ADX_Trend(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        threshold = self.params["threshold"]
        # True Range
        h_l = df["high"] - df["low"]
        h_pc = (df["high"] - df["close"].shift(1)).abs()
        l_pc = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([h_l, h_pc, l_pc], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        # +DM / -DM
        up = df["high"] - df["high"].shift(1)
        down = df["low"].shift(1) - df["low"]
        plus_dm = np.where((up > down) & (up > 0), up, 0)
        minus_dm = np.where((down > up) & (down > 0), down, 0)
        plus_di = 100 * pd.Series(plus_dm, index=df.index).rolling(period).mean() / atr
        minus_di = 100 * pd.Series(minus_dm, index=df.index).rolling(period).mean() / atr
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        df["signal"] = np.where((adx > threshold) & (plus_di > minus_di), 1,
                               np.where((adx > threshold) & (minus_di > plus_di), -1, 0))
        df["signal"] = df["signal"].where(adx.notna(), 0)
        return df


class Supertrend(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        multiplier = self.params["multiplier"]
        hl2 = (df["high"] + df["low"]) / 2
        atr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - df["close"].shift(1)).abs(),
            (df["low"] - df["close"].shift(1)).abs()
        ], axis=1).max(axis=1).rolling(period).mean()
        upper = hl2 + multiplier * atr
        lower = hl2 - multiplier * atr
        st = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(1, index=df.index)
        for i in range(1, len(df)):
            if df["close"].iloc[i] > st.iloc[i-1] if pd.notna(st.iloc[i-1]) else False:
                direction.iloc[i] = 1
                st.iloc[i] = max(lower.iloc[i], st.iloc[i-1] if pd.notna(st.iloc[i-1]) else lower.iloc[i])
            else:
                direction.iloc[i] = -1
                st.iloc[i] = min(upper.iloc[i], st.iloc[i-1] if pd.notna(st.iloc[i-1]) else upper.iloc[i])
        df["signal"] = direction
        df["signal"] = df["signal"].where(atr.notna(), 0)
        return df


class Parabolic_SAR(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        step = self.params["step"]
        max_step = self.params["max"]
        sar = pd.Series(index=df.index, dtype=float)
        ep = pd.Series(index=df.index, dtype=float)
        af = pd.Series(index=df.index, dtype=float)
        trend = pd.Series(1, index=df.index)
        sar.iloc[0] = df["low"].iloc[0]
        ep.iloc[0] = df["high"].iloc[0]
        af.iloc[0] = step
        for i in range(1, len(df)):
            prev_sar = sar.iloc[i-1]
            prev_ep = ep.iloc[i-1]
            prev_af = af.iloc[i-1]
            prev_trend = trend.iloc[i-1]
            new_sar = prev_sar + prev_af * (prev_ep - prev_sar)
            if prev_trend == 1:
                new_sar = min(new_sar, df["low"].iloc[i-1], df["low"].iloc[max(0, i-2)])
                if df["low"].iloc[i] < new_sar:
                    trend.iloc[i] = -1
                    sar.iloc[i] = max(df["high"].iloc[i-1], prev_ep)
                    ep.iloc[i] = df["low"].iloc[i]
                    af.iloc[i] = step
                else:
                    trend.iloc[i] = 1
                    sar.iloc[i] = new_sar
                    if df["high"].iloc[i] > prev_ep:
                        ep.iloc[i] = df["high"].iloc[i]
                        af.iloc[i] = min(prev_af + step, max_step)
                    else:
                        ep.iloc[i] = prev_ep
                        af.iloc[i] = prev_af
            else:
                new_sar = max(new_sar, df["high"].iloc[i-1], df["high"].iloc[max(0, i-2)])
                if df["high"].iloc[i] > new_sar:
                    trend.iloc[i] = 1
                    sar.iloc[i] = min(df["low"].iloc[i-1], prev_ep)
                    ep.iloc[i] = df["high"].iloc[i]
                    af.iloc[i] = step
                else:
                    trend.iloc[i] = -1
                    sar.iloc[i] = new_sar
                    if df["low"].iloc[i] < prev_ep:
                        ep.iloc[i] = df["low"].iloc[i]
                        af.iloc[i] = min(prev_af + step, max_step)
                    else:
                        ep.iloc[i] = prev_ep
                        af.iloc[i] = prev_af
        df["signal"] = trend
        return df


class Price_Above_MA(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        period = self.params["period"]
        ma_type = self.params.get("ma_type", "sma")
        if ma_type == "ema":
            ma = df["close"].ewm(span=period, adjust=False).mean()
        else:
            ma = df["close"].rolling(period).mean()
        df["signal"] = np.where(df["close"] > ma, 1, -1)
        df["signal"] = df["signal"].where(ma.notna(), 0)
        return df
