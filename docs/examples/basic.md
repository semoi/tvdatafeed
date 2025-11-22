# Basic Usage Examples

## Fetching Historical Data

### Simple Example

```python
from tvDatafeed import TvDatafeed, Interval

# Create instance
tv = TvDatafeed()

# Get daily data
df = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_daily,
    n_bars=100
)

print(df.head())
print(f"Columns: {df.columns.tolist()}")
print(f"Shape: {df.shape}")
```

### Multiple Symbols

```python
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

symbols = [
    ('BTCUSDT', 'BINANCE'),
    ('ETHUSDT', 'BINANCE'),
    ('AAPL', 'NASDAQ'),
    ('MSFT', 'NASDAQ'),
]

for symbol, exchange in symbols:
    df = tv.get_hist(symbol, exchange, Interval.in_daily, n_bars=100)
    print(f"{exchange}:{symbol}: {len(df)} bars")
```

### Different Intervals

```python
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

intervals = [
    Interval.in_1_minute,
    Interval.in_5_minute,
    Interval.in_15_minute,
    Interval.in_1_hour,
    Interval.in_4_hour,
    Interval.in_daily,
    Interval.in_weekly,
]

for interval in intervals:
    df = tv.get_hist('BTCUSDT', 'BINANCE', interval, n_bars=10)
    print(f"{interval.name}: {len(df)} bars")
```

## Working with DataFrames

### Basic Analysis

```python
from tvDatafeed import TvDatafeed, Interval
import pandas as pd

tv = TvDatafeed()
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=100)

# Basic statistics
print("Statistics:")
print(df[['open', 'high', 'low', 'close', 'volume']].describe())

# Daily returns
df['returns'] = df['close'].pct_change()
print(f"\nAverage daily return: {df['returns'].mean():.4%}")
print(f"Volatility: {df['returns'].std():.4%}")
```

### Technical Indicators

```python
from tvDatafeed import TvDatafeed, Interval
import pandas as pd

tv = TvDatafeed()
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=100)

# Simple Moving Averages
df['SMA_20'] = df['close'].rolling(window=20).mean()
df['SMA_50'] = df['close'].rolling(window=50).mean()

# Exponential Moving Average
df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()

# RSI (Relative Strength Index)
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

print(df[['close', 'SMA_20', 'SMA_50', 'RSI']].tail(10))
```

### Export Data

```python
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=100)

# To CSV
df.to_csv('btcusdt_daily.csv')

# To Excel
df.to_excel('btcusdt_daily.xlsx')

# To JSON
df.to_json('btcusdt_daily.json', orient='records', date_format='iso')

print("Data exported successfully!")
```

## Symbol Search

### Search Examples

```python
from tvDatafeed import TvDatafeed

tv = TvDatafeed()

# Search all exchanges
results = tv.search_symbol('BTC')
print(f"Found {len(results)} results for 'BTC'")

# Search specific exchange
results = tv.search_symbol('BTC', 'BINANCE')
print(f"Found {len(results)} results for 'BTC' on BINANCE")

# Display formatted results
print(tv.format_search_results(results))
```

### Find Correct Symbol

```python
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

# Don't know the exact symbol? Search first!
results = tv.search_symbol('NVIDIA')

for r in results[:5]:
    full_symbol = f"{r['exchange']}:{r['symbol']}"
    print(f"{full_symbol} - {r['description']} ({r['type']})")

# Then use the correct symbol
df = tv.get_hist('NVDA', 'NASDAQ', Interval.in_daily, n_bars=100)
```

## Error Handling

### Comprehensive Error Handling

```python
from tvDatafeed import TvDatafeed, Interval
from tvDatafeed.exceptions import (
    TvDatafeedError,
    AuthenticationError,
    WebSocketError,
    WebSocketTimeoutError,
    DataNotFoundError,
    DataValidationError
)

def safe_get_hist(tv, symbol, exchange, interval, n_bars):
    """Safely fetch historical data with error handling."""
    try:
        df = tv.get_hist(symbol, exchange, interval, n_bars=n_bars)
        return df

    except DataNotFoundError as e:
        print(f"[ERROR] Symbol not found: {e.symbol} on {e.exchange}")
        return None

    except DataValidationError as e:
        print(f"[ERROR] Invalid input: {e.field}={e.value}")
        print(f"        Reason: {e.reason}")
        return None

    except WebSocketTimeoutError as e:
        print(f"[ERROR] Connection timed out: {e}")
        return None

    except WebSocketError as e:
        print(f"[ERROR] Connection failed: {e}")
        return None

    except TvDatafeedError as e:
        print(f"[ERROR] TvDatafeed error: {e}")
        return None

# Usage
tv = TvDatafeed()

# Valid symbol
df = safe_get_hist(tv, 'BTCUSDT', 'BINANCE', Interval.in_daily, 100)
if df is not None:
    print(f"Got {len(df)} bars")

# Invalid symbol
df = safe_get_hist(tv, 'INVALID', 'BINANCE', Interval.in_daily, 100)
```

### Retry Logic

```python
import time
from tvDatafeed import TvDatafeed, Interval
from tvDatafeed.exceptions import WebSocketError, WebSocketTimeoutError

def fetch_with_retry(tv, symbol, exchange, interval, n_bars, max_retries=3):
    """Fetch data with automatic retry on network errors."""
    for attempt in range(max_retries):
        try:
            return tv.get_hist(symbol, exchange, interval, n_bars=n_bars)
        except (WebSocketError, WebSocketTimeoutError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Attempt {attempt + 1} failed: {e}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"All {max_retries} attempts failed")
                raise

tv = TvDatafeed()
df = fetch_with_retry(tv, 'BTCUSDT', 'BINANCE', Interval.in_daily, 100)
```

## Logging Configuration

### Enable Debug Logging

```python
import logging
from tvDatafeed import TvDatafeed, Interval

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create instance - will show debug info
tv = TvDatafeed()
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=10)
```

### Quiet Mode

```python
from tvDatafeed import TvDatafeed, Interval

# Suppress info messages, only show warnings and errors
tv = TvDatafeed(verbose=False)
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=100)
```

## Timeout Configuration

### Custom Timeouts

```python
from tvDatafeed import TvDatafeed, Interval

# Longer timeout for slow connections
tv = TvDatafeed(ws_timeout=60.0)

# Fetch large amount of data
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_minute, n_bars=5000)
print(f"Got {len(df)} bars")
```

### Environment Variable

```python
import os
os.environ['TV_WS_TIMEOUT'] = '60.0'
os.environ['TV_MAX_RESPONSE_TIME'] = '120.0'

from tvDatafeed import TvDatafeed, Interval

# Uses environment variable values
tv = TvDatafeed()
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_minute, n_bars=5000)
```
