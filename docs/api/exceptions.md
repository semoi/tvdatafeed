# Exceptions

TvDatafeed uses a hierarchy of custom exceptions for precise error handling.

## Exception Hierarchy

```
TvDatafeedError (base)
    |
    +-- AuthenticationError
    |       +-- TwoFactorRequiredError
    |       +-- CaptchaRequiredError
    |
    +-- NetworkError
    |       +-- WebSocketError
    |       |       +-- WebSocketTimeoutError
    |       +-- ConnectionError
    |       +-- RateLimitError
    |
    +-- DataError
    |       +-- DataNotFoundError
    |       +-- DataValidationError
    |       |       +-- InvalidOHLCError
    |       +-- SymbolNotFoundError
    |       +-- InvalidIntervalError
    |
    +-- ThreadingError
    |       +-- LockTimeoutError
    |       +-- ConsumerError
    |
    +-- ConfigurationError
```

---

## Base Exception

### TvDatafeedError

Base exception for all TvDatafeed errors.

```python
class TvDatafeedError(Exception):
    """Base exception for all TvDatafeed errors"""
    pass
```

#### Usage

```python
from tvDatafeed.exceptions import TvDatafeedError

try:
    df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily)
except TvDatafeedError as e:
    # Catches any TvDatafeed-related error
    print(f"TvDatafeed error: {e}")
```

---

## Authentication Exceptions

### AuthenticationError

Raised when authentication fails.

```python
class AuthenticationError(TvDatafeedError):
    def __init__(
        self,
        message: str = "Authentication failed",
        username: Optional[str] = None
    )
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `username` | str | Username that failed authentication |

#### Common Causes

- Invalid credentials
- Account locked
- Network timeout during auth

#### Example

```python
from tvDatafeed.exceptions import AuthenticationError

try:
    tv = TvDatafeed(username='bad', password='wrong')
except AuthenticationError as e:
    print(f"Login failed: {e}")
    if e.username:
        print(f"Username: {e.username}")
```

---

### TwoFactorRequiredError

Raised when 2FA is required but not provided.

```python
class TwoFactorRequiredError(AuthenticationError):
    def __init__(self, method: str = "totp")
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `method` | str | 2FA method required (e.g., "totp") |

#### Example

```python
from tvDatafeed.exceptions import TwoFactorRequiredError

try:
    tv = TvDatafeed(username='user', password='pass')
except TwoFactorRequiredError as e:
    print(f"2FA required: {e.method}")
    # Retry with 2FA code
    tv = TvDatafeed(
        username='user',
        password='pass',
        totp_code=input("Enter 2FA code: ")
    )
```

---

### CaptchaRequiredError

Raised when TradingView requires CAPTCHA verification.

```python
class CaptchaRequiredError(AuthenticationError):
    def __init__(self, username: Optional[str] = None)
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `username` | str | Username that triggered CAPTCHA |

#### Workaround

The exception message includes detailed instructions:

```python
from tvDatafeed.exceptions import CaptchaRequiredError

try:
    tv = TvDatafeed(username='user', password='pass')
except CaptchaRequiredError as e:
    print(e)  # Contains workaround instructions
    # Use auth_token instead
    # See examples/captcha_workaround.py
```

---

## Network Exceptions

### NetworkError

Base class for network-related errors.

```python
class NetworkError(TvDatafeedError):
    pass
```

---

### WebSocketError

Raised when WebSocket connection fails.

```python
class WebSocketError(NetworkError):
    def __init__(
        self,
        message: str = "WebSocket error",
        url: Optional[str] = None
    )
```

#### Example

```python
from tvDatafeed.exceptions import WebSocketError

try:
    df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily)
except WebSocketError as e:
    print(f"Connection failed: {e}")
    # Retry or fallback
```

---

### WebSocketTimeoutError

Raised when WebSocket operation times out.

```python
class WebSocketTimeoutError(WebSocketError):
    def __init__(
        self,
        operation: str = "operation",
        timeout: float = 0
    )
```

#### Example

```python
from tvDatafeed.exceptions import WebSocketTimeoutError

try:
    df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=5000)
except WebSocketTimeoutError as e:
    print(f"Timeout: {e}")
    # Try with longer timeout
    tv = TvDatafeed(ws_timeout=60.0)
```

---

### ConnectionError

Raised when connection cannot be established.

```python
class ConnectionError(NetworkError):
    def __init__(
        self,
        message: str = "Connection failed",
        retry_count: int = 0
    )
```

---

### RateLimitError

Raised when rate limit is exceeded.

```python
class RateLimitError(NetworkError):
    def __init__(
        self,
        limit: int,
        window: int = 60
    )
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `limit` | int | Requests limit |
| `window` | int | Time window in seconds |

---

## Data Exceptions

### DataError

Base class for data-related errors.

```python
class DataError(TvDatafeedError):
    pass
```

---

### DataNotFoundError

Raised when no data is returned.

```python
class DataNotFoundError(DataError):
    def __init__(self, symbol: str, exchange: str)
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `symbol` | str | Symbol that was not found |
| `exchange` | str | Exchange searched |

#### Example

```python
from tvDatafeed.exceptions import DataNotFoundError

try:
    df = tv.get_hist('INVALID', 'BINANCE', Interval.in_daily)
except DataNotFoundError as e:
    print(f"Symbol {e.symbol} not found on {e.exchange}")
    # Use search_symbol to find correct name
    results = tv.search_symbol(e.symbol)
```

---

### DataValidationError

Raised when data validation fails.

```python
class DataValidationError(DataError):
    def __init__(
        self,
        field: str,
        value: any,
        reason: str
    )
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `field` | str | Field that failed validation |
| `value` | any | Invalid value |
| `reason` | str | Reason for failure |

#### Example

```python
from tvDatafeed.exceptions import DataValidationError

try:
    df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=-1)
except DataValidationError as e:
    print(f"Invalid {e.field}: {e.value}")
    print(f"Reason: {e.reason}")
```

---

### InvalidOHLCError

Raised when OHLC data violates expected relationships.

```python
class InvalidOHLCError(DataValidationError):
    def __init__(
        self,
        open_price: float,
        high: float,
        low: float,
        close: float
    )
```

---

### SymbolNotFoundError

Raised when symbol is not found.

```python
class SymbolNotFoundError(DataError):
    def __init__(
        self,
        symbol: str,
        exchange: Optional[str] = None
    )
```

---

### InvalidIntervalError

Raised when interval is invalid.

```python
class InvalidIntervalError(DataError):
    def __init__(
        self,
        interval: str,
        supported: list = None
    )
```

#### Example

```python
from tvDatafeed.exceptions import InvalidIntervalError

try:
    df = tv.get_hist('BTCUSDT', 'BINANCE', 'invalid')
except InvalidIntervalError as e:
    print(f"Invalid interval: {e.interval}")
    # Use Interval enum instead
```

---

## Threading Exceptions

### ThreadingError

Base class for threading-related errors.

```python
class ThreadingError(TvDatafeedError):
    pass
```

---

### LockTimeoutError

Raised when lock acquisition times out.

```python
class LockTimeoutError(ThreadingError):
    def __init__(
        self,
        timeout: float,
        resource: str = "resource"
    )
```

---

### ConsumerError

Raised when consumer encounters an error.

```python
class ConsumerError(ThreadingError):
    def __init__(
        self,
        message: str,
        seis: Optional[str] = None
    )
```

---

## Configuration Exceptions

### ConfigurationError

Raised when configuration is invalid.

```python
class ConfigurationError(TvDatafeedError):
    def __init__(
        self,
        parameter: str,
        value: any,
        reason: str
    )
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `parameter` | str | Parameter name |
| `value` | any | Invalid value |
| `reason` | str | Reason for failure |

#### Example

```python
from tvDatafeed.exceptions import ConfigurationError

try:
    tv = TvDatafeed(ws_timeout=-100)
except ConfigurationError as e:
    print(f"Invalid config: {e.parameter}={e.value}")
    print(f"Reason: {e.reason}")
```

---

## Error Handling Patterns

### Comprehensive Error Handling

```python
from tvDatafeed import TvDatafeed, Interval
from tvDatafeed.exceptions import (
    AuthenticationError,
    TwoFactorRequiredError,
    CaptchaRequiredError,
    WebSocketError,
    WebSocketTimeoutError,
    DataNotFoundError,
    DataValidationError,
    ConfigurationError
)

def fetch_data_safely(symbol, exchange, interval, n_bars):
    try:
        tv = TvDatafeed()
        return tv.get_hist(symbol, exchange, interval, n_bars=n_bars)

    except CaptchaRequiredError:
        print("CAPTCHA required - see workaround in docs")
        return None

    except TwoFactorRequiredError:
        print("2FA required - provide totp_secret or totp_code")
        return None

    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
        return None

    except WebSocketTimeoutError as e:
        print(f"Timeout: {e}")
        print("Try increasing TV_WS_TIMEOUT environment variable")
        return None

    except WebSocketError as e:
        print(f"Connection error: {e}")
        return None

    except DataNotFoundError as e:
        print(f"No data for {e.symbol} on {e.exchange}")
        return None

    except DataValidationError as e:
        print(f"Invalid input: {e.field}={e.value}")
        return None

    except ConfigurationError as e:
        print(f"Config error: {e.parameter}={e.value}")
        return None
```

### Retry Pattern

```python
import time
from tvDatafeed.exceptions import WebSocketError, WebSocketTimeoutError

def fetch_with_retry(tv, symbol, exchange, interval, max_retries=3):
    for attempt in range(max_retries):
        try:
            return tv.get_hist(symbol, exchange, interval, n_bars=100)
        except (WebSocketError, WebSocketTimeoutError) as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # Exponential backoff
                print(f"Retry {attempt + 1}/{max_retries} in {wait}s...")
                time.sleep(wait)
            else:
                raise
```
