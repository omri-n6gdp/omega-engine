"""Seasonality and calendar strategies."""
import pandas as pd
import numpy as np
from strategies.base import Strategy


class DayOfWeek(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        day = self.params["day"]
        df["signal"] = np.where(df.index.dayofweek == day, 1, 0)
        return df


class TurnOfMonth(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        before = self.params["days_before"]
        after = self.params["days_after"]
        dom = df.index.day
        eom = df.index + pd.offsets.MonthEnd(0)
        is_eom = (eom.day - dom) < before
        is_bom = dom <= after
        df["signal"] = np.where(is_eom | is_bom, 1, 0)
        return df


class MonthOfYear(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        month = self.params["month"]
        df["signal"] = np.where(df.index.month == month, 1, 0)
        return df


class SellInMay(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        month = df.index.month
        df["signal"] = np.where((month >= 11) | (month <= 4), 1, 0)
        return df


class FirstFiveDays(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        dom = df.index.day
        month = df.index.month
        df["signal"] = np.where((month == 1) & (dom <= 5), 1, 0)
        return df
