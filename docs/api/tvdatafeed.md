# TvDatafeed

The main class for fetching historical data from TradingView.

## Class Definition

```python
class TvDatafeed:
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        auth_token: Optional[str] = None,
        totp_secret: Optional[str] = None,
        totp_code: Optional[str] = None,
        ws_timeout: Optional[float] = None,
        verbose: Optional[bool] = None,
    ) -> None
```

## Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `username` | str | None | TradingView username |
| `password` | str | None | TradingView password |
| `auth_token` | str | None | Pre-obtained authentication token (bypasses login) |
| `totp_secret` | str | None | TOTP secret for automatic 2FA code generation |
| `totp_code` | str | None | Manual 6-digit 2FA code |
| `ws_timeout` | float | None | WebSocket timeout in seconds |
| `verbose` | bool | None | Enable verbose logging |

### Authentication Options

There are several ways to authenticate:

=== "Username/Password"

    ```python
    tv = TvDatafeed(
        username='your_username',
        password='your_password'
    )
    ```

=== "With 2FA (TOTP Secret)"

    ```python
    tv = TvDatafeed(
        username='your_username',
        password='your_password',
        totp_secret='YOUR_BASE32_SECRET'
    )
    ```

=== "With 2FA (Manual Code)"

    ```python
    tv = TvDatafeed(
        username='your_username',
        password='your_password',
        totp_code='123456'
    )
    ```

=== "Pre-obtained Token"

    ```python
    # Use when CAPTCHA is required
    tv = TvDatafeed(auth_token='your_auth_token')
    ```

=== "Environment Variables"

    ```python
    import os
    from dotenv import load_dotenv

    load_dotenv()

    tv = TvDatafeed(
        username=os.getenv('TV_USERNAME'),
        password=os.getenv('TV_PASSWORD'),
        totp_secret=os.getenv('TV_TOTP_SECRET')
    )
    ```

### Timeout Configuration

Priority for WebSocket timeout:

1. `ws_timeout` parameter (highest priority)
2. `TV_WS_TIMEOUT` environment variable
3. `NetworkConfig.recv_timeout`
4. Default: 5 seconds

```python
# Custom timeout
tv = TvDatafeed(ws_timeout=30.0)

# Or via environment
# export TV_WS_TIMEOUT=30.0
tv = TvDatafeed()
```

### Verbose Logging

Control logging verbosity:

```python
# Quiet mode (production)
tv = TvDatafeed(verbose=False)

# Verbose mode (debugging)
tv = TvDatafeed(verbose=True)

# Or via environment
# export TV_VERBOSE=false
tv = TvDatafeed()
```

## Methods

### get_hist

Fetch historical OHLCV data from TradingView.

```python
def get_hist(
    self,
    symbol: str,
    exchange: str = "NSE",
    interval: Interval = Interval.in_daily,
    n_bars: Optional[int] = None,
    fut_contract: Optional[int] = None,
    extended_session: bool = False,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Optional[pd.DataFrame]
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbol` | str | **required** | Symbol name (e.g., 'BTCUSDT', 'AAPL') |
| `exchange` | str | "NSE" | Exchange name (e.g., 'BINANCE', 'NASDAQ') |
| `interval` | Interval | in_daily | Chart interval |
| `n_bars` | int | None | Number of bars (max 5000) |
| `fut_contract` | int | None | Futures contract number |
| `extended_session` | bool | False | Include extended trading hours |
| `start_date` | datetime | None | Start date for date range query |
| `end_date` | datetime | None | End date for date range query |

!!! warning "Mutually Exclusive Parameters"
    `n_bars` and `start_date`/`end_date` are mutually exclusive. Use one or the other.

#### Returns

| Type | Description |
|------|-------------|
| `pd.DataFrame` | DataFrame with columns: symbol, datetime (index), open, high, low, close, volume |
| `None` | If no data is available |

#### Examples

=== "Basic Usage"

    ```python
    from tvDatafeed import TvDatafeed, Interval

    tv = TvDatafeed()

    # Get 100 daily bars
    df = tv.get_hist(
        symbol='BTCUSDT',
        exchange='BINANCE',
        interval=Interval.in_daily,
        n_bars=100
    )

    print(df.head())
    #                          symbol     open     high      low    close       volume
    # datetime
    # 2024-01-01  BINANCE:BTCUSDT  42000.0  42500.0  41500.0  42200.0  1234567890.0
    ```

=== "Date Range Query"

    ```python
    from datetime import datetime
    from tvDatafeed import TvDatafeed, Interval

    tv = TvDatafeed()

    df = tv.get_hist(
        symbol='AAPL',
        exchange='NASDAQ',
        interval=Interval.in_1_hour,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31)
    )

    # Access timezone metadata
    print(f"Timezone: {df.attrs.get('timezone', 'Not set')}")
    ```

=== "Futures Contract"

    ```python
    tv = TvDatafeed()

    # Front month continuous contract
    df = tv.get_hist(
        symbol='CRUDEOIL',
        exchange='MCX',
        interval=Interval.in_daily,
        fut_contract=1,
        n_bars=100
    )
    ```

=== "Extended Session"

    ```python
    tv = TvDatafeed()

    # Include pre/post market data
    df = tv.get_hist(
        symbol='AAPL',
        exchange='NASDAQ',
        interval=Interval.in_15_minute,
        extended_session=True,
        n_bars=200
    )
    ```

#### Exceptions

| Exception | Condition |
|-----------|-----------|
| `DataValidationError` | Invalid symbol, exchange, n_bars, or date range |
| `InvalidIntervalError` | Invalid interval type |
| `WebSocketError` | Connection failure |
| `WebSocketTimeoutError` | Operation timeout |
| `DataNotFoundError` | No data available |

---

### search_symbol

Search for symbols on TradingView.

```python
def search_symbol(
    self,
    text: str,
    exchange: str = ''
) -> list
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | str | **required** | Search query (e.g., 'BTC', 'AAPL') |
| `exchange` | str | '' | Limit to specific exchange |

#### Returns

| Type | Description |
|------|-------------|
| `list` | List of dictionaries with symbol information |

Each dictionary contains:

- `symbol`: Symbol name
- `exchange`: Exchange name
- `description`: Symbol description
- `type`: Asset type (stock, crypto, etc.)

#### Examples

```python
tv = TvDatafeed()

# Search all exchanges
results = tv.search_symbol('BTC')

# Search specific exchange
results = tv.search_symbol('BTC', 'BINANCE')

# Use results
for r in results[:5]:
    full_symbol = f"{r['exchange']}:{r['symbol']}"
    print(f"{full_symbol} - {r['description']}")
```

---

### format_search_results

Format search results for display.

```python
@staticmethod
def format_search_results(
    results: list,
    max_results: int = 10
) -> str
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `results` | list | **required** | Results from search_symbol() |
| `max_results` | int | 10 | Maximum results to format |

#### Example

```python
tv = TvDatafeed()
results = tv.search_symbol('ETH', 'BINANCE')
print(tv.format_search_results(results))
```

---

### is_valid_date_range

Validate a date range for historical queries.

```python
@staticmethod
def is_valid_date_range(
    start: datetime,
    end: datetime
) -> bool
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `start` | datetime | Start date |
| `end` | datetime | End date |

#### Returns

`True` if the date range is valid, `False` otherwise.

#### Validation Rules

- Start date must be before end date
- Neither date can be in the future
- Both dates must be after 2000-01-01

---

## Interval

Enum class for chart intervals.

```python
class Interval(enum.Enum):
    in_1_minute = "1"
    in_3_minute = "3"
    in_5_minute = "5"
    in_15_minute = "15"
    in_30_minute = "30"
    in_45_minute = "45"
    in_1_hour = "1H"
    in_2_hour = "2H"
    in_3_hour = "3H"
    in_4_hour = "4H"
    in_daily = "1D"
    in_weekly = "1W"
    in_monthly = "1M"
```

### Usage

```python
from tvDatafeed import Interval

# Use enum values
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=100)

# Available intervals
for i in Interval:
    print(f"{i.name}: {i.value}")
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `token` | str | Authentication token |
| `ws_timeout` | float | WebSocket timeout in seconds |
| `verbose` | bool | Verbose logging enabled |
| `max_response_time` | float | Maximum cumulative response time |
| `session` | str | Session ID |
| `chart_session` | str | Chart session ID |

---

## Class Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `__ws_timeout` | 5 | Default WebSocket timeout |
| `__ws_max_retries` | 3 | Max WebSocket connection retries |
| `__ws_retry_base_delay` | 2.0 | Base retry delay (seconds) |
| `__ws_retry_max_delay` | 10.0 | Max retry delay (seconds) |
| `__max_response_time` | 60.0 | Default max response time |
