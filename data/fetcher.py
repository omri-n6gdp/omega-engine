"""Yahoo Finance data fetcher with caching and polite rate limiting."""
import time
import yfinance as yf
import pandas as pd
from typing import Dict, Optional
from data.database import DatabaseManager


class DataFetcher:
    """Fetches and caches Yahoo Finance data."""

    def __init__(self, db: DatabaseManager, delay: float = 1.5):
        self.db = db
        self.delay = delay

    def fetch(self, ticker: str, timeframe: str = "1d",
              period: str = "5y", force: bool = False) -> pd.DataFrame:
        if not force:
            cached = self.db.get_price_data(ticker, timeframe)
            if not cached.empty and len(cached) > 100:
                print(f"  [Cache] {ticker} {timeframe}: {len(cached)} bars")
                return cached

        print(f"[Fetch] {ticker} {timeframe} ...", end=" ", flush=True)

        for attempt in range(5):
            try:
                t = yf.Ticker(ticker)
                df = t.history(period=period, interval=timeframe)
                if df.empty:
                    print("NO DATA")
                    return pd.DataFrame()
                df = df.dropna()
                self.db.save_price_data(df, ticker, timeframe)
                time.sleep(self.delay)
                print(f"OK ({len(df)} bars)")
                return self.db.get_price_data(ticker, timeframe)
            except Exception as e:
                err_str = str(e).lower()
                if "too many requests" in err_str or "rate limited" in err_str or "429" in err_str:
                    wait = (2 ** attempt) * 5  # 5, 10, 20, 40, 80 seconds
                    print(f"RATE LIMITED (attempt {attempt+1}/5), waiting {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"ERROR: {e}")
                    return pd.DataFrame()

        print("FAILED after 5 attempts")
        return pd.DataFrame()

    def fetch_all(self, tickers, timeframe="1d", period="5y") -> Dict[str, pd.DataFrame]:
        out = {}
        for t in tickers:
            df = self.fetch(t, timeframe, period)
            if not df.empty:
                out[t] = df
        return out
