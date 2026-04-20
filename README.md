# crypto-backtest

个人用的加密货币回测工具, 之前在cex上跑策略时候写的

## 安装

```
pip install -r requirements.txt
```

## 用法

```python
from backtest import BacktestEngine, load_ohlcv
from backtest.strategy import SMACross

data = load_ohlcv('BTC/USDT', '1d', limit=365)
engine = BacktestEngine(data)
result = engine.run(SMACross(7, 25))
print(engine.get_metrics(result))
```

自定义策略继承Strategy就行:

```python
from backtest.strategy import Strategy

class MyStrategy(Strategy):
    def generate_signals(self, data):
        # 1=买 -1=卖 0=不动
        ...
```

内置了几个策略, 看strategy.py

examples里面有btc的回测notebook

## todo
- 接defi perp数据
- 多币种
- 滑点模拟 (现在没做)
