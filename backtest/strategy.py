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


class BollingerBand(Strategy):
    """布林带策略 — 价格触及下轨买入，触及上轨卖出"""

    def __init__(self, period: int = 20, num_std: float = 2.0):
        self.period = period
        self.num_std = num_std

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        ma = data['close'].rolling(self.period).mean()
        std = data['close'].rolling(self.period).std()
        upper = ma + self.num_std * std
        lower = ma - self.num_std * std

        signals = pd.Series(0, index=data.index)

        prev_close = data['close'].shift(1)
        prev_lower = lower.shift(1)
        prev_upper = upper.shift(1)

        signals[(prev_close >= prev_lower) & (data['close'] < lower)] = 1
        signals[(prev_close <= prev_upper) & (data['close'] > upper)] = -1

        return signals
