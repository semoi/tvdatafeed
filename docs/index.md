# TvDatafeed Documentation

**TvDatafeed** is a Python library for fetching historical and real-time market data from TradingView.

## Features

- **Historical Data**: Retrieve up to 5000 bars of OHLCV data
- **Real-time Data**: Monitor multiple symbols with live updates
- **2FA Support**: Full support for two-factor authentication (TOTP)
- **Date Range Queries**: Fetch data for specific time periods
- **Multiple Timeframes**: Minutes, hours, days, weeks, and months
- **Threading Support**: Process live data with callback functions

## Quick Start

### Installation

```bash
pip install tvdatafeed
```

### Basic Usage

```python
from tvDatafeed import TvDatafeed, Interval

# Create instance (unauthenticated - limited data)
tv = TvDatafeed()

# Get historical data
df = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_1_hour,
    n_bars=100
)

print(df.head())
```

### With Authentication

```python
from tvDatafeed import TvDatafeed, Interval

# Authenticated access
tv = TvDatafeed(
    username='your_username',
    password='your_password'
)

# Get more data with authenticated access
df = tv.get_hist('AAPL', 'NASDAQ', Interval.in_daily, n_bars=1000)
```

### With 2FA

```python
from tvDatafeed import TvDatafeed, Interval

# With TOTP secret (recommended)
tv = TvDatafeed(
    username='your_username',
    password='your_password',
    totp_secret='YOUR_TOTP_SECRET'  # From authenticator setup
)

# Or with manual code
tv = TvDatafeed(
    username='your_username',
    password='your_password',
    totp_code='123456'  # Current 6-digit code
)
```

## Supported Intervals

| Interval | Description |
|----------|-------------|
| `Interval.in_1_minute` | 1 minute |
| `Interval.in_3_minute` | 3 minutes |
| `Interval.in_5_minute` | 5 minutes |
| `Interval.in_15_minute` | 15 minutes |
| `Interval.in_30_minute` | 30 minutes |
| `Interval.in_45_minute` | 45 minutes |
| `Interval.in_1_hour` | 1 hour |
| `Interval.in_2_hour` | 2 hours |
| `Interval.in_3_hour` | 3 hours |
| `Interval.in_4_hour` | 4 hours |
| `Interval.in_daily` | Daily |
| `Interval.in_weekly` | Weekly |
| `Interval.in_monthly` | Monthly |

## Environment Variables

TvDatafeed supports configuration via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `TV_USERNAME` | TradingView username | None |
| `TV_PASSWORD` | TradingView password | None |
| `TV_TOTP_SECRET` | TOTP secret for 2FA | None |
| `TV_2FA_CODE` | Manual 2FA code | None |
| `TV_WS_TIMEOUT` | WebSocket timeout (seconds) | 5 |
| `TV_MAX_RESPONSE_TIME` | Max response wait time | 60 |
| `TV_VERBOSE` | Enable verbose logging | true |

## Next Steps

- [Installation Guide](getting-started/installation.md)
- [Quick Start Tutorial](getting-started/quickstart.md)
- [API Reference](api/index.md)
- [Examples](examples/basic.md)
