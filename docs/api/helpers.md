# Helper Classes

This page documents the helper classes used by TvDatafeed for live data processing.

## Seis

**S**ymbol-**E**xchange-**I**nterval **S**et - A container for a unique combination of symbol, exchange, and interval.

### Class Definition

```python
class Seis:
    def __init__(
        self,
        symbol: str,
        exchange: str,
        interval: Interval
    )
```

### Constructor Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | str | Ticker symbol (e.g., 'BTCUSDT') |
| `exchange` | str | Exchange name (e.g., 'BINANCE') |
| `interval` | Interval | Chart interval |

### Properties

| Property | Type | Access | Description |
|----------|------|--------|-------------|
| `symbol` | str | read-only | Ticker symbol |
| `exchange` | str | read-only | Exchange name |
| `interval` | Interval | read-only | Chart interval |
| `tvdatafeed` | TvDatafeedLive | read/write | Parent TvDatafeedLive reference |

### Methods

#### new_consumer

Create a new consumer for this Seis.

```python
def new_consumer(
    self,
    callback: Callable,
    timeout: int = -1
) -> Union[Consumer, bool]
```

##### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `callback` | Callable | **required** | Callback function |
| `timeout` | int | -1 | Max wait time |

##### Returns

`Consumer` object or `False` if timeout.

##### Raises

| Exception | Condition |
|-----------|-----------|
| `NameError` | No TvDatafeedLive reference |

##### Example

```python
def my_callback(seis, data):
    print(f"New data for {seis.symbol}")

consumer = seis.new_consumer(my_callback)
```

---

#### del_consumer

Remove a consumer from this Seis.

```python
def del_consumer(
    self,
    consumer: Consumer,
    timeout: int = -1
) -> bool
```

##### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `consumer` | Consumer | **required** | Consumer to remove |
| `timeout` | int | -1 | Max wait time |

##### Returns

`True` if successful, `False` if timeout.

---

#### get_hist

Get historical data for this Seis.

```python
def get_hist(
    self,
    n_bars: int = 10,
    timeout: int = -1
) -> Union[pd.DataFrame, bool]
```

##### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_bars` | int | 10 | Number of bars |
| `timeout` | int | -1 | Max wait time |

##### Returns

`pd.DataFrame` with OHLCV data or `False` if timeout.

##### Example

```python
# Get 100 bars for this Seis
df = seis.get_hist(n_bars=100)
```

---

#### del_seis

Remove this Seis from TvDatafeedLive.

```python
def del_seis(
    self,
    timeout: int = -1
) -> bool
```

##### Returns

`True` if successful, `False` if timeout.

##### Example

```python
# Remove seis from live feed
seis.del_seis()
```

---

#### get_consumers

Get list of consumers for this Seis.

```python
def get_consumers(self) -> list
```

##### Returns

Thread-safe copy of consumer list.

---

#### is_new_data

Check if data is newer than last update.

```python
def is_new_data(self, data: pd.DataFrame) -> bool
```

##### Returns

`True` if data is new, `False` otherwise.

!!! note "Internal Method"
    This method is primarily used internally by TvDatafeedLive.

---

### String Representations

```python
seis = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)

repr(seis)  # Seis("BTCUSDT","BINANCE",Interval.in_1_hour)
str(seis)   # symbol='BTCUSDT',exchange='BINANCE',interval='in_1_hour'
```

### Equality Comparison

Two Seis instances are equal if they have the same symbol, exchange, and interval:

```python
seis1 = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
seis2 = Seis('BTCUSDT', 'BINANCE', Interval.in_1_hour)
seis3 = Seis('ETHUSDT', 'BINANCE', Interval.in_1_hour)

seis1 == seis2  # True
seis1 == seis3  # False
```

### Thread Safety

Seis uses internal locks for thread-safe operations:

| Lock | Protects |
|------|----------|
| `_consumers_lock` | Consumer list modifications |
| `_updated_lock` | Last update timestamp |

---

## Consumer

A threaded callback handler for processing live data.

### Class Definition

```python
class Consumer(threading.Thread):
    def __init__(
        self,
        seis: Seis,
        callback: Callable[[Seis, pd.DataFrame], None]
    )
```

### Constructor Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `seis` | Seis | The Seis to receive data from |
| `callback` | Callable | Function to call with new data |

### Callback Signature

```python
def callback(seis: Seis, data: pd.DataFrame) -> None:
    """
    Called when new data is available.

    Parameters
    ----------
    seis : Seis
        The Seis that received data
    data : pd.DataFrame
        Single row DataFrame with OHLCV data
    """
    pass
```

### Properties

| Property | Type | Access | Description |
|----------|------|--------|-------------|
| `seis` | Seis | read/write | Seis reference (thread-safe) |
| `callback` | Callable | read/write | Callback function (thread-safe) |
| `name` | str | read-only | Thread name (auto-generated) |

### Methods

#### start

Start the consumer thread.

```python
def start(self) -> None
```

!!! note "Called Automatically"
    `TvDatafeedLive.new_consumer()` calls this automatically.

---

#### stop

Stop the consumer thread.

```python
def stop(self) -> None
```

##### Example

```python
consumer.stop()
```

---

#### put

Add data to the processing queue.

```python
def put(self, data: pd.DataFrame) -> None
```

##### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | pd.DataFrame | Data to process |

!!! note "Internal Method"
    This is called by TvDatafeedLive when new data arrives.

---

#### del_consumer

Stop and remove from Seis.

```python
def del_consumer(
    self,
    timeout: int = -1
) -> bool
```

##### Returns

`True` if successful, `False` if timeout.

---

### String Representations

```python
consumer = Consumer(seis, my_callback)

repr(consumer)  # Consumer(Seis("BTCUSDT","BINANCE",Interval.in_1_hour),my_callback)
str(consumer)   # Seis("BTCUSDT","BINANCE",Interval.in_1_hour),callback=my_callback
```

### Thread Model

```
Consumer Thread
    |
    +-- Queue.get(timeout=1.0)  # Wait for data
    |       |
    |       +-- data = None -> Exit thread
    |       +-- data = DataFrame -> callback(seis, data)
    |
    +-- Check _stopped flag periodically
    |
    +-- On exception in callback:
            +-- Log error
            +-- Remove from Seis
            +-- Exit thread
```

### Thread Safety

| Lock | Protects |
|------|----------|
| `_lock` | `_seis`, `_callback`, `_stopped` |

### Lifecycle

```python
# 1. Create consumer
consumer = Consumer(seis, callback)

# 2. Start thread (done by new_consumer)
consumer.start()

# 3. Consumer processes data in background
# ... time passes ...

# 4. Stop consumer
consumer.stop()

# 5. Wait for thread to finish
consumer.join()
```

---

## Utility Functions

The `utils` module provides helper functions used throughout TvDatafeed.

### generate_session_id

Generate a random session ID.

```python
def generate_session_id(
    prefix: str = "qs",
    length: int = 12
) -> str
```

#### Example

```python
from tvDatafeed.utils import generate_session_id

session = generate_session_id()  # "qs_abcdefghijkl"
```

---

### generate_chart_session_id

Generate a chart session ID.

```python
def generate_chart_session_id(length: int = 12) -> str
```

#### Example

```python
from tvDatafeed.utils import generate_chart_session_id

chart_session = generate_chart_session_id()  # "cs_abcdefghijkl"
```

---

### retry_with_backoff

Retry a function with exponential backoff.

```python
def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
) -> T
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `func` | Callable | **required** | Function to retry |
| `max_retries` | int | 3 | Maximum attempts |
| `base_delay` | float | 1.0 | Initial delay (seconds) |
| `max_delay` | float | 60.0 | Maximum delay (seconds) |
| `exceptions` | tuple | (Exception,) | Exceptions to catch |
| `on_retry` | Callable | None | Callback on each retry |

#### Example

```python
from tvDatafeed.utils import retry_with_backoff

def fetch_data():
    # May fail temporarily
    return api.get_data()

# Retry up to 3 times with exponential backoff
data = retry_with_backoff(
    fetch_data,
    max_retries=3,
    base_delay=2.0,
    exceptions=(ConnectionError, TimeoutError)
)
```

---

### mask_sensitive_data

Mask sensitive data for logging.

```python
def mask_sensitive_data(
    data: str,
    visible_chars: int = 4,
    mask_char: str = '*'
) -> str
```

#### Example

```python
from tvDatafeed.utils import mask_sensitive_data

token = "my_secret_token_12345"
masked = mask_sensitive_data(token)  # "***************12345"
```

---

### ContextTimer

Context manager for timing code blocks.

```python
class ContextTimer:
    def __init__(
        self,
        name: str = "Operation",
        logger_instance: Optional[logging.Logger] = None
    )
```

#### Example

```python
from tvDatafeed.utils import ContextTimer

with ContextTimer("Data fetch"):
    df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily)
# Logs: "Data fetch took 1.23s"
```

---

## Validators

The `validators` module provides input validation functions.

### Validators.validate_symbol

Validate a symbol name.

```python
@staticmethod
def validate_symbol(
    symbol: str,
    allow_formatted: bool = True
) -> str
```

#### Example

```python
from tvDatafeed.validators import Validators

# Valid symbols
Validators.validate_symbol('BTCUSDT')           # 'BTCUSDT'
Validators.validate_symbol('BINANCE:BTCUSDT')   # 'BINANCE:BTCUSDT'

# Invalid - raises DataValidationError
Validators.validate_symbol('')
```

---

### Validators.validate_exchange

Validate an exchange name.

```python
@staticmethod
def validate_exchange(exchange: str) -> str
```

---

### Validators.validate_n_bars

Validate number of bars.

```python
@staticmethod
def validate_n_bars(
    n_bars: int,
    max_bars: int = 5000
) -> int
```

---

### Validators.validate_timeout

Validate timeout value.

```python
@staticmethod
def validate_timeout(timeout: Union[int, float]) -> float
```

---

### Validators.validate_ohlc

Validate OHLC relationships.

```python
@staticmethod
def validate_ohlc(
    open_price: float,
    high: float,
    low: float,
    close: float,
    raise_on_error: bool = True
) -> bool
```

#### Example

```python
from tvDatafeed.validators import Validators

# Valid OHLC
Validators.validate_ohlc(100, 110, 95, 105)  # True

# Invalid - high < open
Validators.validate_ohlc(100, 90, 85, 95)    # Raises InvalidOHLCError
```

---

### Validators.validate_credentials

Validate authentication credentials.

```python
@staticmethod
def validate_credentials(
    username: Optional[str],
    password: Optional[str]
) -> bool
```

#### Returns

- `True` if both provided
- `False` if neither provided
- Raises `ConfigurationError` if only one provided

---

### Validators.validate_date_range

Validate date range for queries.

```python
@staticmethod
def validate_date_range(
    start_date: Optional[datetime],
    end_date: Optional[datetime]
) -> tuple
```

#### Validation Rules

- Both must be provided together (or both None)
- Start must be before end
- Neither can be in the future
- Both must be after 2000-01-01
