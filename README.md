# TvDatafeed

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/rongardF/tvdatafeed/workflows/Tests/badge.svg)](https://github.com/rongardF/tvdatafeed/actions)

A Python package for downloading historical and live data from TradingView. Supports up to 5000 bars of historical data on any supported timeframe, plus real-time data streaming.

> **NOTE:** This is a fork of the original [TvDatafeed](https://github.com/rongardF/tvdatafeed.git) project by StreamAlpha, with live data retrieving features and improved reliability.

## ✨ Features

- 📊 Download up to 5000 historical bars
- ⚡ Real-time data streaming with callbacks
- 🔒 Secure authentication (environment variables supported)
- 🌍 Support for stocks, crypto, forex, commodities
- 📈 13 timeframes (1m to 1M)
- 🧵 Thread-safe live feed implementation
- 🐼 Returns pandas DataFrames
- 🔍 Symbol search functionality

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Historical Data](#historical-data)
  - [Live Data Feed](#live-data-feed)
  - [Symbol Search](#symbol-search)
- [Configuration](#configuration)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation

### From GitHub (recommended)

```bash
pip install --upgrade --no-cache-dir git+https://github.com/rongardF/tvdatafeed.git
```

### From source

```bash
git clone https://github.com/rongardF/tvdatafeed.git
cd tvdatafeed
pip install -e .
```

## ⚡ Quick Start

```python
from tvDatafeed import TvDatafeed, Interval

# Initialize (no login required for limited access)
tv = TvDatafeed()

# Download historical data
df = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_1_hour,
    n_bars=100
)

print(df.head())
```

## 📚 Usage

### Authentication

#### No Authentication (Limited Access)

```python
tv = TvDatafeed()
```

⚠️ Some symbols may not be available without authentication.

#### With Authentication (Recommended)

**Option 1: Environment Variables (Secure)**

```bash
export TV_USERNAME="your_username"
export TV_PASSWORD="your_password"
```

```python
import os
tv = TvDatafeed(
    username=os.getenv('TV_USERNAME'),
    password=os.getenv('TV_PASSWORD')
)
```

**Option 2: Direct Credentials**

```python
tv = TvDatafeed(username='your_username', password='your_password')
```

⚠️ **Security Note:** Never hardcode credentials in production code.

### Historical Data

#### Basic Usage

```python
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

# Crypto
btc_data = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=100)

# Stocks
aapl_data = tv.get_hist('AAPL', 'NASDAQ', Interval.in_daily, n_bars=365)

# Futures continuous contract
nifty_futures = tv.get_hist('NIFTY', 'NSE', Interval.in_1_hour, n_bars=1000, fut_contract=1)

# Extended hours
extended_data = tv.get_hist('AAPL', 'NASDAQ', Interval.in_1_hour, n_bars=100, extended_session=True)
```

#### Parameters

```python
tv.get_hist(
    symbol: str,           # Symbol name
    exchange: str,         # Exchange name
    interval: Interval,    # Time interval
    n_bars: int = 10,      # Number of bars (max 5000)
    fut_contract: int = None,  # Futures contract (1=front, 2=next)
    extended_session: bool = False  # Include extended hours
) -> pd.DataFrame
```

### Live Data Feed

For real-time data monitoring with callbacks:

```python
from tvDatafeed import TvDatafeedLive, Interval
import time

# Initialize (authentication required)
tvl = TvDatafeedLive(username='your_username', password='your_password')

# Create SEIS (Symbol-Exchange-Interval Set)
seis = tvl.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)

# Define callback
def on_new_data(seis, data):
    print(f"New data: {data.iloc[-1]['close']}")

# Register callback
consumer = tvl.new_consumer(seis, on_new_data)

# Let it run
time.sleep(300)  # 5 minutes

# Cleanup
tvl.del_consumer(consumer)
tvl.del_seis(seis)
```

See [examples/live_feed.py](examples/live_feed.py) for detailed usage.

### Symbol Search

Find exact symbol names:

```python
# Search for Bitcoin on Binance
results = tv.search_symbol('BTC', 'BINANCE')

for result in results:
    print(f"{result['symbol']} - {result['description']}")

# Output:
# BTCUSDT - Bitcoin / TetherUS
# BTCUSD - Bitcoin / US Dollar
# ...
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file (see [.env.example](.env.example) for all options):

```bash
# Authentication
TV_USERNAME=your_username
TV_PASSWORD=your_password

# Network (optional)
TV_CONNECT_TIMEOUT=10.0
TV_RECV_TIMEOUT=30.0
TV_MAX_RETRIES=3

# Debug
TV_DEBUG=false
```

### Using Configuration

```python
from tvDatafeed.config import TvDatafeedConfig

# Load from environment variables
config = TvDatafeedConfig.from_env()

# Or use defaults
config = TvDatafeedConfig.default()
```

## 📝 Examples

Check out the [examples/](examples/) directory:

- **[basic_usage.py](examples/basic_usage.py)** - Getting started guide
- **[live_feed.py](examples/live_feed.py)** - Real-time data monitoring
- **[error_handling.py](examples/error_handling.py)** - Robust error handling

Run examples:

```bash
python examples/basic_usage.py
```

## 🕐 Supported Timeframes

```python
Interval.in_1_minute   # 1 minute
Interval.in_3_minute   # 3 minutes
Interval.in_5_minute   # 5 minutes
Interval.in_15_minute  # 15 minutes
Interval.in_30_minute  # 30 minutes
Interval.in_45_minute  # 45 minutes
Interval.in_1_hour     # 1 hour
Interval.in_2_hour     # 2 hours
Interval.in_3_hour     # 3 hours
Interval.in_4_hour     # 4 hours
Interval.in_daily      # 1 day
Interval.in_weekly     # 1 week
Interval.in_monthly    # 1 month
```

## 🌍 Common Exchanges

- **Crypto:** `BINANCE`, `COINBASE`, `KRAKEN`, `BITFINEX`
- **US Stocks:** `NASDAQ`, `NYSE`, `AMEX`
- **Indian Markets:** `NSE`, `BSE`
- **Commodities:** `MCX`, `NYMEX`, `COMEX`
- **Forex:** `FX`, `OANDA`

## 🔧 Troubleshooting

### "No data returned"

**Possible causes:**
- Symbol name incorrect → Use `search_symbol()` to find exact name
- Symbol not available on specified exchange
- Authentication required for this symbol

**Solution:**
```python
# Find correct symbol name
results = tv.search_symbol('BTC', 'BINANCE')
print(results[0]['symbol'])  # Use this symbol
```

### "Authentication failed"

**Possible causes:**
- Incorrect username/password
- 2FA enabled (not yet supported)
- Credentials not in environment variables

**Solution:**
```bash
export TV_USERNAME="your_username"
export TV_PASSWORD="your_password"
```

### "Timeout errors"

**Possible causes:**
- Slow internet connection
- TradingView servers busy

**Solution:**
```python
# Increase timeout (requires config module)
from tvDatafeed.config import NetworkConfig
config = NetworkConfig(recv_timeout=60.0)
```

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
tv = TvDatafeed()
tv.ws_debug = True
```

## 🧪 Testing

Run tests:

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=tvDatafeed --cov-report=html

# Run specific tests
pytest tests/unit/test_seis.py
```

## 📊 Integration with TA-Lib

TvDatafeed returns pandas DataFrames, making it easy to use with [TA-Lib](https://github.com/mrjbq7/ta-lib):

```python
import talib

df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=100)

# Calculate indicators
df['SMA_20'] = talib.SMA(df['close'], timeperiod=20)
df['RSI'] = talib.RSI(df['close'], timeperiod=14)
df['MACD'], df['MACD_signal'], df['MACD_hist'] = talib.MACD(df['close'])
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick start:**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests
5. Run tests (`pytest`)
6. Commit (`git commit -m 'feat: add amazing feature'`)
7. Push (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original project by [StreamAlpha](https://github.com/StreamAlpha)
- TradingView for providing the data
- All contributors

## ⚠️ Disclaimer

This is an **unofficial** library. Use at your own risk. Always verify data accuracy before making trading decisions.

---

## 📺 Video Tutorials

**v1.2 Tutorial with Backtrader Integration**

[![Watch the video](https://img.youtube.com/vi/f76dOZW2gwI/hqdefault.jpg)](https://youtu.be/f76dOZW2gwI)

**Full Tutorial**

[![Watch the video](https://img.shields.io/vi/qDrXmb2ZRjo/hqdefault.jpg)](https://youtu.be/qDrXmb2ZRjo)

---

## 🐛 Reporting Issues

Before creating an issue:

1. **Search existing issues** - Your problem might already be reported
2. **Use latest version** - Update to the latest version
3. **Provide details:**
   - Python version
   - Operating system
   - Full error traceback
   - Minimal code to reproduce
   - Expected vs actual behavior

See [CONTRIBUTING.md](CONTRIBUTING.md) for issue templates.

---

**Support the original author:**

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/StreamAlpha)
