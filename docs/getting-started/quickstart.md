# Quick Start

This guide will get you up and running with TvDatafeed in minutes.

## Basic Usage

### 1. Create TvDatafeed Instance

```python
from tvDatafeed import TvDatafeed, Interval

# Unauthenticated (limited data)
tv = TvDatafeed()
```

### 2. Fetch Historical Data

```python
# Get 100 daily bars for Bitcoin
df = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_daily,
    n_bars=100
)

print(df.head())
```

Output:
```
                          symbol     open     high      low    close       volume
datetime
2024-01-01  BINANCE:BTCUSDT  42000.0  42500.0  41500.0  42200.0  1234567890.0
2024-01-02  BINANCE:BTCUSDT  42200.0  43000.0  42000.0  42800.0  1345678901.0
...
```

### 3. Search for Symbols

```python
# Find Bitcoin symbols on Binance
results = tv.search_symbol('BTC', 'BINANCE')

for r in results[:5]:
    print(f"{r['exchange']}:{r['symbol']} - {r['description']}")
```

## Different Timeframes

```python
# 1 minute bars
df_1m = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_minute, n_bars=100)

# 1 hour bars
df_1h = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=100)

# Daily bars
df_1d = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=100)

# Weekly bars
df_1w = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_weekly, n_bars=100)
```

## Different Asset Classes

### Stocks

```python
# Apple on NASDAQ
df = tv.get_hist('AAPL', 'NASDAQ', Interval.in_daily, n_bars=100)

# Microsoft
df = tv.get_hist('MSFT', 'NASDAQ', Interval.in_daily, n_bars=100)
```

### Crypto

```python
# Bitcoin
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=100)

# Ethereum
df = tv.get_hist('ETHUSDT', 'BINANCE', Interval.in_1_hour, n_bars=100)
```

### Forex

```python
# EUR/USD
df = tv.get_hist('EURUSD', 'FX', Interval.in_daily, n_bars=100)

# GBP/USD
df = tv.get_hist('GBPUSD', 'FX', Interval.in_daily, n_bars=100)
```

### Futures

```python
# Crude Oil continuous front month
df = tv.get_hist('CRUDEOIL', 'MCX', Interval.in_daily, n_bars=100, fut_contract=1)

# Nifty futures
df = tv.get_hist('NIFTY', 'NSE', Interval.in_daily, n_bars=100, fut_contract=1)
```

## Date Range Queries

```python
from datetime import datetime

# Get data for specific date range
df = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_1_hour,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)

print(f"Got {len(df)} bars from {df.index[0]} to {df.index[-1]}")
```

## Extended Trading Hours

```python
# Include pre-market and after-hours data
df = tv.get_hist(
    symbol='AAPL',
    exchange='NASDAQ',
    interval=Interval.in_15_minute,
    n_bars=100,
    extended_session=True
)
```

## Error Handling

```python
from tvDatafeed.exceptions import DataNotFoundError, WebSocketError

try:
    df = tv.get_hist('INVALID', 'BINANCE', Interval.in_daily)
except DataNotFoundError as e:
    print(f"Symbol not found: {e}")
except WebSocketError as e:
    print(f"Connection error: {e}")
```

## Next Steps

- [Authentication Guide](authentication.md) - Get more data with a TradingView account
- [API Reference](../api/index.md) - Complete API documentation
- [Examples](../examples/basic.md) - More code examples
