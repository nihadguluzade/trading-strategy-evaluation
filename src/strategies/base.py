from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    """
    Abstract Base Class for all trading strategies.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Subclasses must implement this.
        It should take a DataFrame with OHLCV data and return
        the same DataFrame with a new 'Signal' column (1 or 0).
        """
        pass

    def calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardized calculation for Market and Strategy returns.
        """
        # 1. Calculate underlying market % change
        df['Market_Returns'] = df['Close'].pct_change()

        # 2. Apply the Signal to the Returns with a 1-period SHIFT (t+1)
        # This prevents look-ahead bias as defined in the project doc
        df['Strategy_Returns'] = df['Signal'].shift(1) * df['Market_Returns']

        return df

    def execute(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        The main pipeline: Clean, Generate Signals, Calculate Returns.
        """
        data = df.copy()
        data = self.generate_signals(data)
        data = self.calculate_returns(data)
        return data