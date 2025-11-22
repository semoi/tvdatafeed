# API Reference

This section provides detailed documentation for all public classes, methods, and functions in TvDatafeed.

## Core Classes

### Data Retrieval

| Class | Description |
|-------|-------------|
| [TvDatafeed](tvdatafeed.md) | Main class for fetching historical data from TradingView |
| [TvDatafeedLive](tvdatafeedlive.md) | Extended class with real-time data monitoring |

### Helper Classes

| Class | Description |
|-------|-------------|
| [Seis](helpers.md#seis) | Symbol-Exchange-Interval Set container |
| [Consumer](helpers.md#consumer) | Callback handler for live data processing |
| [Interval](tvdatafeed.md#interval) | Enum for chart intervals |

### Configuration

| Class | Description |
|-------|-------------|
| [NetworkConfig](configuration.md#networkconfig) | Network and WebSocket configuration |
| [AuthConfig](configuration.md#authconfig) | Authentication configuration |
| [DataConfig](configuration.md#dataconfig) | Data processing configuration |
| [ThreadingConfig](configuration.md#threadingconfig) | Threading configuration |

### Exceptions

| Exception | Description |
|-----------|-------------|
| [TvDatafeedError](exceptions.md#tvdatafeederror) | Base exception |
| [AuthenticationError](exceptions.md#authenticationerror) | Authentication failures |
| [WebSocketError](exceptions.md#websocketerror) | WebSocket issues |
| [DataNotFoundError](exceptions.md#datanotfounderror) | Data not available |

## Module Structure

```
tvDatafeed/
    __init__.py          # Public exports
    main.py              # TvDatafeed class
    datafeed.py          # TvDatafeedLive class
    seis.py              # Seis class
    consumer.py          # Consumer class
    exceptions.py        # Custom exceptions
    config.py            # Configuration classes
    utils.py             # Utility functions
    validators.py        # Input validators
```

## Quick Links

- [TvDatafeed.get_hist()](tvdatafeed.md#get_hist) - Get historical data
- [TvDatafeed.search_symbol()](tvdatafeed.md#search_symbol) - Search for symbols
- [TvDatafeedLive.new_seis()](tvdatafeedlive.md#new_seis) - Add symbol to live feed
- [TvDatafeedLive.new_consumer()](tvdatafeedlive.md#new_consumer) - Add callback for live data

## Usage Patterns

### Historical Data Only

Use `TvDatafeed` for one-time data fetching:

```python
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=100)
```

### Live Data Monitoring

Use `TvDatafeedLive` for continuous monitoring:

```python
from tvDatafeed import TvDatafeedLive, Interval

def on_new_data(seis, data):
    print(f"New data for {seis.symbol}: {data}")

tv = TvDatafeedLive()
seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)
consumer = tv.new_consumer(seis, on_new_data)

# Later, cleanup
tv.del_tvdatafeed()
```

### Error Handling

```python
from tvDatafeed import TvDatafeed, Interval
from tvDatafeed.exceptions import (
    AuthenticationError,
    WebSocketError,
    DataNotFoundError
)

tv = TvDatafeed()

try:
    df = tv.get_hist('INVALID', 'EXCHANGE', Interval.in_daily)
except DataNotFoundError as e:
    print(f"Symbol not found: {e}")
except WebSocketError as e:
    print(f"Connection error: {e}")
except AuthenticationError as e:
    print(f"Auth error: {e}")
```
