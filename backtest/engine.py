import pandas as pd
import numpy as np
from typing import Optional


class BacktestEngine:
    """回测引擎 — 基于事件驱动的简易回测框架"""

    def __init__(self, data: pd.DataFrame, initial_capital: float = 10000.0,
                 commission: float = 0.001,
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None):
        self.data = data.copy()
        if start_date:
            self.data = self.data[self.data.index >= pd.Timestamp(start_date)]
        if end_date:
            self.data = self.data[self.data.index <= pd.Timestamp(end_date)]
        if self.data.empty:
            raise ValueError('过滤后数据为空，请检查日期范围')
        self.initial_capital = initial_capital
        self.commission = commission
        self.positions = 0.0
        self.capital = initial_capital
        self.equity_curve = []
        self.trades = []

    def run(self, strategy) -> pd.DataFrame:
        signals = strategy.generate_signals(self.data)
        self.data['signal'] = signals

        self.capital = self.initial_capital
        self.positions = 0.0
        self.equity_curve = []
        self.trades = []

        for i in range(len(self.data)):
            row = self.data.iloc[i]
            price = row['close']
            signal = row['signal']

            if signal == 1 and self.positions == 0:
                qty = (self.capital * 0.95) / price
                cost = qty * price * (1 + self.commission)
                if cost <= self.capital:
                    self.positions = qty
                    self.capital -= cost
                    self.trades.append({
                        'date': self.data.index[i],
                        'side': 'buy',
                        'price': price,
                        'qty': qty
                    })

            elif signal == -1 and self.positions > 0:
                revenue = self.positions * price * (1 - self.commission)
                self.capital += revenue
                self.trades.append({
                    'date': self.data.index[i],
                    'side': 'sell',
                    'price': price,
                    'qty': self.positions
                })
                self.positions = 0.0

            equity = self.capital + self.positions * price
            self.equity_curve.append({
                'date': self.data.index[i],
                'equity': equity,
                'capital': self.capital,
                'positions': self.positions,
                'price': price
            })

        result = pd.DataFrame(self.equity_curve).set_index('date')
        return result

    def get_metrics(self, result: pd.DataFrame) -> dict:
        returns = result['equity'].pct_change().dropna()
        total_return = (result['equity'].iloc[-1] / self.initial_capital) - 1
        days = (result.index[-1] - result.index[0]).days
        annual_return = (1 + total_return) ** (365 / max(days, 1)) - 1

        sharpe = (returns.mean() / returns.std()) * np.sqrt(365) if returns.std() > 0 else 0

        rolling_max = result['equity'].expanding().max()
        drawdown = (result['equity'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        win_trades = 0
        total_trades = len(self.trades) // 2
        for i in range(0, len(self.trades) - 1, 2):
            if self.trades[i + 1]['price'] > self.trades[i]['price']:
                win_trades += 1

        return {
            '总收益率': f'{total_return:.2%}',
            '年化收益率': f'{annual_return:.2%}',
            '夏普比率': f'{sharpe:.3f}',
            '最大回撤': f'{max_drawdown:.2%}',
            '交易次数': total_trades,
            '胜率': f'{win_trades / max(total_trades, 1):.2%}',
            '最终资金': f'{result["equity"].iloc[-1]:.2f}'
        }
