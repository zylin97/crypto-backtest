import pandas as pd
import numpy as np
from abc import ABC, abstractmethod


class Strategy(ABC):

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        pass


class SMACross(Strategy):

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
    # 布林带, 下轨买上轨卖

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


class FundingRateArb(Strategy):
    # funding rate套利, 在binance上跑了一年多大概8-15%年化
    # 现在想搬到链上试试

    def __init__(self, entry_threshold: float = 0.01,
                 exit_threshold: float = 0.002,
                 lookback: int = 8):
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.lookback = lookback

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=data.index)

        if 'funding_rate' not in data.columns:
            returns = data['close'].pct_change()
            vol = returns.rolling(24).std()
            data = data.copy()
            data['funding_rate'] = (returns.rolling(self.lookback).mean() * 3 +
                                    vol * 0.5).clip(-0.05, 0.05)

        avg_rate = data['funding_rate'].rolling(self.lookback).mean()

        for i in range(self.lookback, len(data)):
            if avg_rate.iloc[i] > self.entry_threshold:
                signals.iloc[i] = 1
            elif avg_rate.iloc[i] < self.exit_threshold:
                signals.iloc[i] = -1

        return signals


class VolatilityRegime(Strategy):
    # 波动率regime检测, 简化版
    # 低波动用动量, 高波动用均值回归
    # 实盘版用的hmm, 这里用分位数近似差不多够了

    def __init__(self, vol_window: int = 20, vol_quantile: float = 0.7,
                 momentum_window: int = 14, mean_rev_window: int = 10):
        self.vol_window = vol_window
        self.vol_quantile = vol_quantile
        self.momentum_window = momentum_window
        self.mean_rev_window = mean_rev_window

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        returns = data['close'].pct_change()
        realized_vol = returns.rolling(self.vol_window).std() * np.sqrt(365)

        expanding_quantile = realized_vol.expanding(min_periods=60).quantile(self.vol_quantile)
        is_high_vol = realized_vol > expanding_quantile

        momentum = data['close'].pct_change(self.momentum_window)
        ma = data['close'].rolling(self.mean_rev_window).mean()
        deviation = (data['close'] - ma) / ma

        signals = pd.Series(0, index=data.index)

        for i in range(max(60, self.vol_window, self.momentum_window), len(data)):
            if is_high_vol.iloc[i]:
                if deviation.iloc[i] < -0.03:
                    signals.iloc[i] = 1
                elif deviation.iloc[i] > 0.03:
                    signals.iloc[i] = -1
            else:
                if momentum.iloc[i] > 0.05:
                    signals.iloc[i] = 1
                elif momentum.iloc[i] < -0.03:
                    signals.iloc[i] = -1

        return signals


class VolumeWeightedMomentum(Strategy):
    # vwap偏离+放量检测
    # 放量突破比缩量突破可靠的多

    def __init__(self, vwap_period: int = 20, vol_mult: float = 1.5,
                 momentum_period: int = 10):
        self.vwap_period = vwap_period
        self.vol_mult = vol_mult
        self.momentum_period = momentum_period

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        vwap = ((typical_price * data['volume']).rolling(self.vwap_period).sum() /
                data['volume'].rolling(self.vwap_period).sum())

        vol_ma = data['volume'].rolling(self.vwap_period).mean()
        vol_std = data['volume'].rolling(self.vwap_period).std()
        volume_surge = data['volume'] > (vol_ma + vol_std * self.vol_mult)

        price_above_vwap = data['close'] > vwap
        momentum = data['close'].pct_change(self.momentum_period)

        signals = pd.Series(0, index=data.index)

        buy_cond = price_above_vwap & volume_surge & (momentum > 0.02)
        sell_cond = (~price_above_vwap) & volume_surge & (momentum < -0.02)

        signals[buy_cond] = 1
        signals[sell_cond] = -1

        return signals
