"""Abstract base class for all strategies."""
from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd
import numpy as np


class Strategy(ABC):
    """Base class for trading strategies."""

    def __init__(self, name: str, params: Dict[str, Any]):
        self.name = name
        self.params = params

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals.
        Input: DataFrame with columns [open, high, low, close, volume]
        Output: DataFrame with column 'signal' ∈ {-1, 0, 1}
        Must NOT use future data (no lookahead bias).
        """
        pass

    def param_key(self) -> str:
        import json
        return json.dumps(self.params, sort_keys=True)

    def __repr__(self):
        return f"{self.name}({self.params})"
