# Configuration

TvDatafeed provides dataclass-based configuration for flexible customization.

## Overview

Configuration is organized into specialized classes:

| Class | Purpose |
|-------|---------|
| `NetworkConfig` | WebSocket and HTTP settings |
| `AuthConfig` | Authentication settings |
| `DataConfig` | Data processing settings |
| `ThreadingConfig` | Threading settings |
| `TvDatafeedConfig` | Aggregate configuration |

All configuration can be loaded from environment variables.

---

## NetworkConfig

Configuration for WebSocket and HTTP connections.

```python
@dataclass
class NetworkConfig:
    ws_url: str = "wss://data.tradingview.com/socket.io/websocket"
    ws_headers: Dict[str, str] = field(default_factory=lambda: {
        "Origin": "https://data.tradingview.com"
    })
    connect_timeout: float = 10.0
    send_timeout: float = 5.0
    recv_timeout: float = 30.0
    max_retries: int = 3
    base_retry_delay: float = 2.0
    max_retry_delay: float = 60.0
    requests_per_minute: int = 60
```

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `ws_url` | str | wss://data.tradingview.com/... | WebSocket URL |
| `ws_headers` | dict | {"Origin": ...} | WebSocket headers |
| `connect_timeout` | float | 10.0 | Connection timeout (seconds) |
| `send_timeout` | float | 5.0 | Send timeout (seconds) |
| `recv_timeout` | float | 30.0 | Receive timeout (seconds) |
| `max_retries` | int | 3 | Maximum retry attempts |
| `base_retry_delay` | float | 2.0 | Initial retry delay (seconds) |
| `max_retry_delay` | float | 60.0 | Maximum retry delay (seconds) |
| `requests_per_minute` | int | 60 | Rate limit |

### Environment Variables

| Variable | Maps To |
|----------|---------|
| `TV_WS_URL` | `ws_url` |
| `TV_CONNECT_TIMEOUT` | `connect_timeout` |
| `TV_SEND_TIMEOUT` | `send_timeout` |
| `TV_RECV_TIMEOUT` | `recv_timeout` |
| `TV_MAX_RETRIES` | `max_retries` |
| `TV_BASE_RETRY_DELAY` | `base_retry_delay` |
| `TV_MAX_RETRY_DELAY` | `max_retry_delay` |
| `TV_REQUESTS_PER_MINUTE` | `requests_per_minute` |

### Usage

```python
from tvDatafeed.config import NetworkConfig

# Default configuration
config = NetworkConfig()

# From environment variables
config = NetworkConfig.from_env()

# Custom configuration
config = NetworkConfig(
    recv_timeout=60.0,
    max_retries=5,
    base_retry_delay=5.0
)
```

---

## AuthConfig

Configuration for authentication.

```python
@dataclass
class AuthConfig:
    sign_in_url: str = 'https://www.tradingview.com/accounts/signin/'
    signin_headers: Dict[str, str] = field(default_factory=lambda: {
        'Referer': 'https://www.tradingview.com'
    })
    username: Optional[str] = None
    password: Optional[str] = None
    two_factor_code: Optional[str] = None
```

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `sign_in_url` | str | https://...signin/ | Sign-in endpoint |
| `signin_headers` | dict | {"Referer": ...} | Auth request headers |
| `username` | str | None | TradingView username |
| `password` | str | None | TradingView password |
| `two_factor_code` | str | None | 2FA code |

### Environment Variables

| Variable | Maps To |
|----------|---------|
| `TV_USERNAME` | `username` |
| `TV_PASSWORD` | `password` |
| `TV_2FA_CODE` | `two_factor_code` |

### Usage

```python
from tvDatafeed.config import AuthConfig

# From environment variables
config = AuthConfig.from_env()

# Check if credentials are provided
if config.username and config.password:
    print("Authenticated mode")
else:
    print("Unauthenticated mode")
```

---

## DataConfig

Configuration for data processing.

```python
@dataclass
class DataConfig:
    max_bars: int = 5000
    default_bars: int = 10
    validate_data: bool = True
    fill_missing_volume: str = 'zero'
    timezone: str = 'UTC'
```

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_bars` | int | 5000 | Maximum bars per request |
| `default_bars` | int | 10 | Default bars if not specified |
| `validate_data` | bool | True | Validate OHLCV data |
| `fill_missing_volume` | str | 'zero' | How to fill missing volume |
| `timezone` | str | 'UTC' | Default timezone |

### Environment Variables

| Variable | Maps To |
|----------|---------|
| `TV_MAX_BARS` | `max_bars` |
| `TV_DEFAULT_BARS` | `default_bars` |
| `TV_VALIDATE_DATA` | `validate_data` |
| `TV_FILL_MISSING_VOLUME` | `fill_missing_volume` |
| `TV_TIMEZONE` | `timezone` |

### Usage

```python
from tvDatafeed.config import DataConfig

# From environment variables
config = DataConfig.from_env()

print(f"Max bars: {config.max_bars}")
print(f"Validation: {'enabled' if config.validate_data else 'disabled'}")
```

---

## ThreadingConfig

Configuration for TvDatafeedLive threading.

```python
@dataclass
class ThreadingConfig:
    retry_limit: int = 50
    retry_sleep: float = 0.1
    shutdown_timeout: float = 10.0
```

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `retry_limit` | int | 50 | Max data fetch retries |
| `retry_sleep` | float | 0.1 | Sleep between retries (seconds) |
| `shutdown_timeout` | float | 10.0 | Graceful shutdown timeout (seconds) |

### Environment Variables

| Variable | Maps To |
|----------|---------|
| `TV_RETRY_LIMIT` | `retry_limit` |
| `TV_RETRY_SLEEP` | `retry_sleep` |
| `TV_SHUTDOWN_TIMEOUT` | `shutdown_timeout` |

### Usage

```python
from tvDatafeed.config import ThreadingConfig

# From environment variables
config = ThreadingConfig.from_env()

print(f"Retry limit: {config.retry_limit}")
print(f"Shutdown timeout: {config.shutdown_timeout}s")
```

---

## TvDatafeedConfig

Aggregate configuration containing all sub-configurations.

```python
@dataclass
class TvDatafeedConfig:
    network: NetworkConfig = field(default_factory=NetworkConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    data: DataConfig = field(default_factory=DataConfig)
    threading: ThreadingConfig = field(default_factory=ThreadingConfig)
    debug: bool = False
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `network` | NetworkConfig | Network configuration |
| `auth` | AuthConfig | Auth configuration |
| `data` | DataConfig | Data configuration |
| `threading` | ThreadingConfig | Threading configuration |
| `debug` | bool | Enable debug mode |

### Class Methods

#### from_env()

Create configuration from all environment variables.

```python
@classmethod
def from_env(cls) -> 'TvDatafeedConfig':
    return cls(
        network=NetworkConfig.from_env(),
        auth=AuthConfig.from_env(),
        data=DataConfig.from_env(),
        threading=ThreadingConfig.from_env(),
        debug=os.getenv('TV_DEBUG', 'false').lower() == 'true',
    )
```

#### default()

Create configuration with default values.

```python
@classmethod
def default(cls) -> 'TvDatafeedConfig':
    return cls()
```

### Usage

```python
from tvDatafeed.config import TvDatafeedConfig

# Load all configuration from environment
config = TvDatafeedConfig.from_env()

# Access sub-configurations
print(f"WebSocket timeout: {config.network.recv_timeout}s")
print(f"Username: {config.auth.username}")
print(f"Max bars: {config.data.max_bars}")
print(f"Debug mode: {config.debug}")

# Or use defaults
config = TvDatafeedConfig.default()
```

---

## Global Default Configuration

A pre-created default configuration instance is available:

```python
from tvDatafeed.config import DEFAULT_CONFIG

# Use default values
print(DEFAULT_CONFIG.network.recv_timeout)  # 30.0
print(DEFAULT_CONFIG.data.max_bars)         # 5000
```

---

## Environment Variable Reference

### Complete List

```bash
# Network
TV_WS_URL=wss://data.tradingview.com/socket.io/websocket
TV_CONNECT_TIMEOUT=10.0
TV_SEND_TIMEOUT=5.0
TV_RECV_TIMEOUT=30.0
TV_MAX_RETRIES=3
TV_BASE_RETRY_DELAY=2.0
TV_MAX_RETRY_DELAY=60.0
TV_REQUESTS_PER_MINUTE=60

# Authentication
TV_USERNAME=your_username
TV_PASSWORD=your_password
TV_2FA_CODE=123456
TV_TOTP_SECRET=YOUR_BASE32_SECRET

# Data
TV_MAX_BARS=5000
TV_DEFAULT_BARS=10
TV_VALIDATE_DATA=true
TV_FILL_MISSING_VOLUME=zero
TV_TIMEZONE=UTC

# Threading
TV_RETRY_LIMIT=50
TV_RETRY_SLEEP=0.1
TV_SHUTDOWN_TIMEOUT=10.0

# Misc
TV_DEBUG=false
TV_VERBOSE=true
TV_WS_TIMEOUT=5.0
TV_MAX_RESPONSE_TIME=60.0
```

### Example .env File

```bash
# .env file for TvDatafeed

# Authentication (required for full access)
TV_USERNAME=your_email@example.com
TV_PASSWORD=your_secure_password
TV_TOTP_SECRET=JBSWY3DPEHPK3PXP

# Timeouts (increase for slow connections)
TV_WS_TIMEOUT=30.0
TV_MAX_RESPONSE_TIME=120.0

# Logging
TV_VERBOSE=false
TV_DEBUG=false
```

### Loading .env File

```python
from dotenv import load_dotenv
from tvDatafeed import TvDatafeed
from tvDatafeed.config import TvDatafeedConfig
import os

# Load .env file
load_dotenv()

# Configuration is now loaded from environment
config = TvDatafeedConfig.from_env()

# TvDatafeed also reads from environment
tv = TvDatafeed(
    username=os.getenv('TV_USERNAME'),
    password=os.getenv('TV_PASSWORD'),
    totp_secret=os.getenv('TV_TOTP_SECRET')
)
```
