import pandas as pd
import numpy as np
from abc import ABC, abstractmethod


class Strategy(ABC):
    """策略基类"""

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        pass


class SMACross(Strategy):
    """SMA均线交叉策略"""

    def __init__(self, fast_period: int = 10, slow_period: int = 30):
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        fast_ma = data['close'].rolling(self.fast_period).mean()
        slow_ma = data['close'].rolling(self.slow_period).mean()

        signals = pd.Series(0, index=data.index)

        prev_fast = fast_ma.shift(1)
        prev_slow = slow_ma.shift(1)

        signals[(prev_fast <= prev_slow) & (fast_ma > slow_ma)] = 1
        signals[(prev_fast >= prev_slow) & (fast_ma < slow_ma)] = -1

        return signals
