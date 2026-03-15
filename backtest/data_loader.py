import ccxt
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


def load_ohlcv(symbol: str = 'BTC/USDT', timeframe: str = '1d',
               exchange_id: str = 'binance',
               start_date: Optional[str] = None,
               limit: int = 500) -> pd.DataFrame:
    """从交易所获取OHLCV数据"""

    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({'enableRateLimit': True})

    since = None
    if start_date:
        since = exchange.parse8601(start_date + 'T00:00:00Z')

    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    return df


def load_csv(filepath: str) -> pd.DataFrame:
    """从CSV文件加载数据"""

    df = pd.read_csv(filepath, parse_dates=['timestamp'], index_col='timestamp')
    required = ['open', 'high', 'low', 'close', 'volume']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f'缺少必需列: {missing}')

    return df
