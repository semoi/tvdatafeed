# TvDatafeedLive

Extended class for real-time data monitoring with callback support.

`TvDatafeedLive` inherits from `TvDatafeed` and adds live data feed capabilities using threading.

## Class Definition

```python
class TvDatafeedLive(TvDatafeed):
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None
    )
```

## Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `username` | str | None | TradingView username |
| `password` | str | None | TradingView password |

!!! note "Inherited Parameters"
    `TvDatafeedLive` inherits all authentication options from `TvDatafeed`, including 2FA support.

## Architecture

```
TvDatafeedLive
    |
    +-- Main Thread (monitors intervals)
    |       |
    |       +-- Fetches new data when interval expires
    |       +-- Pushes data to consumers
    |
    +-- Consumer Threads (one per callback)
            |
            +-- Receives data from queue
            +-- Executes callback function
```

## Methods

### new_seis

Create and add a new Seis (Symbol-Exchange-Interval Set) to the live feed.

```python
def new_seis(
    self,
    symbol: str,
    exchange: str,
    interval: Interval,
    timeout: int = -1
) -> Union[Seis, bool]
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbol` | str | **required** | Ticker symbol |
| `exchange` | str | **required** | Exchange name |
| `interval` | Interval | **required** | Chart interval |
| `timeout` | int | -1 | Max wait time (-1 = blocking) |

#### Returns

| Type | Description |
|------|-------------|
| `Seis` | The created or existing Seis object |
| `False` | If timeout expired |

#### Exceptions

| Exception | Condition |
|-----------|-----------|
| `ValueError` | Symbol/exchange not found on TradingView |

#### Example

```python
from tvDatafeed import TvDatafeedLive, Interval

tv = TvDatafeedLive()

# Add symbol to live feed
seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)

# If Seis already exists, same instance is returned
seis2 = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)
assert seis is seis2
```

---

### del_seis

Remove a Seis from the live feed.

```python
def del_seis(
    self,
    seis: Seis,
    timeout: int = -1
) -> bool
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `seis` | Seis | **required** | Seis to remove |
| `timeout` | int | -1 | Max wait time (-1 = blocking) |

#### Returns

`True` if successful, `False` if timeout expired.

#### Exceptions

| Exception | Condition |
|-----------|-----------|
| `ValueError` | Seis not in live feed |

#### Example

```python
seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)

# Later, remove it
tv.del_seis(seis)
```

---

### new_consumer

Create a new consumer with a callback function for a Seis.

```python
def new_consumer(
    self,
    seis: Seis,
    callback: Callable[[Seis, pd.DataFrame], None],
    timeout: int = -1
) -> Union[Consumer, bool]
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `seis` | Seis | **required** | Seis to monitor |
| `callback` | Callable | **required** | Function to call with new data |
| `timeout` | int | -1 | Max wait time (-1 = blocking) |

#### Callback Signature

```python
def callback(seis: Seis, data: pd.DataFrame) -> None:
    """
    Parameters
    ----------
    seis : Seis
        The Seis that received new data
    data : pd.DataFrame
        DataFrame with single row of OHLCV data
    """
    pass
```

#### Returns

| Type | Description |
|------|-------------|
| `Consumer` | The created Consumer object |
| `False` | If timeout expired |

#### Exceptions

| Exception | Condition |
|-----------|-----------|
| `ValueError` | Seis not in live feed |

#### Example

```python
def on_new_data(seis, data):
    """Called when new bar is available"""
    print(f"[{seis.symbol}] New data at {data.index[0]}")
    print(f"  Open: {data['open'].iloc[0]}")
    print(f"  High: {data['high'].iloc[0]}")
    print(f"  Low: {data['low'].iloc[0]}")
    print(f"  Close: {data['close'].iloc[0]}")
    print(f"  Volume: {data['volume'].iloc[0]}")

tv = TvDatafeedLive()
seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)
consumer = tv.new_consumer(seis, on_new_data)
```

---

### del_consumer

Remove a consumer from its Seis.

```python
def del_consumer(
    self,
    consumer: Consumer,
    timeout: int = -1
) -> bool
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `consumer` | Consumer | **required** | Consumer to remove |
| `timeout` | int | -1 | Max wait time (-1 = blocking) |

#### Returns

`True` if successful, `False` if timeout expired.

#### Example

```python
consumer = tv.new_consumer(seis, callback)

# Later, remove the consumer
tv.del_consumer(consumer)
```

---

### get_hist

Get historical data (inherited from TvDatafeed with thread-safe locking).

```python
def get_hist(
    self,
    symbol: str,
    exchange: str = "NSE",
    interval: Interval = Interval.in_daily,
    n_bars: int = 10,
    fut_contract: Optional[int] = None,
    extended_session: bool = False,
    timeout: int = -1
) -> Union[pd.DataFrame, bool]
```

#### Parameters

Same as `TvDatafeed.get_hist()` plus:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout` | int | -1 | Max wait time (-1 = blocking) |

#### Returns

`pd.DataFrame` with OHLCV data, or `False` if timeout expired.

#### Example

```python
tv = TvDatafeedLive()

# Safe to call while live feed is running
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=100)
```

---

### del_tvdatafeed

Stop all threads and cleanup resources.

```python
def del_tvdatafeed(self) -> None
```

#### Example

```python
tv = TvDatafeedLive()
seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)
consumer = tv.new_consumer(seis, callback)

# ... use the live feed ...

# Cleanup when done
tv.del_tvdatafeed()
```

---

## Complete Example

```python
from tvDatafeed import TvDatafeedLive, Interval
import time

def btc_handler(seis, data):
    """Handle BTC updates"""
    close = data['close'].iloc[0]
    print(f"BTC: ${close:,.2f}")

def eth_handler(seis, data):
    """Handle ETH updates"""
    close = data['close'].iloc[0]
    print(f"ETH: ${close:,.2f}")

# Create live feed
tv = TvDatafeedLive()

try:
    # Add symbols to monitor
    btc_seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)
    eth_seis = tv.new_seis('ETHUSDT', 'BINANCE', Interval.in_1_minute)

    # Add callbacks
    btc_consumer = tv.new_consumer(btc_seis, btc_handler)
    eth_consumer = tv.new_consumer(eth_seis, eth_handler)

    # Let it run for a while
    print("Monitoring BTC and ETH... Press Ctrl+C to stop")
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nShutting down...")

finally:
    # Always cleanup
    tv.del_tvdatafeed()
    print("Done")
```

---

## Threading Model

### Locks

| Lock | Protects | Description |
|------|----------|-------------|
| `_lock` | `_sat`, public operations | Main lock for all operations |
| `_thread_lock` | `_main_thread` | Access to main thread reference |

### Thread Safety

- All public methods acquire locks before modifying state
- Consumer callbacks run in separate threads
- Exception in callback stops that consumer only
- Graceful shutdown with configurable timeouts

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `RETRY_LIMIT` | 50 | Max retries for data fetch |
| `SHUTDOWN_TIMEOUT` | 10.0 | Main thread shutdown timeout |
| `CONSUMER_STOP_TIMEOUT` | 5.0 | Consumer thread stop timeout |

---

## Best Practices

### 1. Always Cleanup

```python
tv = TvDatafeedLive()
try:
    # ... use live feed ...
finally:
    tv.del_tvdatafeed()
```

### 2. Handle Callback Exceptions

```python
def safe_callback(seis, data):
    try:
        # Your logic here
        process_data(data)
    except Exception as e:
        logging.error(f"Error processing {seis.symbol}: {e}")
        # Don't re-raise - keeps consumer alive
```

### 3. Use Timeout for Non-Blocking

```python
# Non-blocking with 5 second timeout
seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute, timeout=5)
if seis is False:
    print("Timeout - operation didn't complete in 5 seconds")
```

### 4. Multiple Callbacks per Symbol

```python
seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)

# Multiple consumers for same seis
consumer1 = tv.new_consumer(seis, log_to_file)
consumer2 = tv.new_consumer(seis, send_alert)
consumer3 = tv.new_consumer(seis, update_database)
```
