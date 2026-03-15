# crypto-backtest

加密货币量化回测框架。支持自定义策略、多交易所数据源。

## 功能

- 事件驱动回测引擎
- 内置策略：SMA均线交叉、布林带
- 支持Binance、OKX等交易所数据
- 绩效指标：夏普比率、最大回撤、胜率

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

```python
from backtest import BacktestEngine, load_ohlcv
from backtest.strategy import SMACross

data = load_ohlcv('BTC/USDT', '1d', limit=365)
engine = BacktestEngine(data, initial_capital=10000)
result = engine.run(SMACross(fast_period=7, slow_period=25))
print(engine.get_metrics(result))
```

## 策略开发

继承 `Strategy` 基类，实现 `generate_signals` 方法：

```python
from backtest.strategy import Strategy

class MyStrategy(Strategy):
    def generate_signals(self, data):
        # 返回信号序列: 1=买入, -1=卖出, 0=持仓
        ...
```

详见 `examples/` 目录。
