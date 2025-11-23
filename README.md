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

**Option 3: Pre-obtained Token (for CAPTCHA issues)**

If TradingView requires CAPTCHA verification, you'll need to extract the token manually:

```bash
export TV_AUTH_TOKEN="your_token_here"
```

```python
import os
tv = TvDatafeed(auth_token=os.getenv('TV_AUTH_TOKEN'))
```

See [CAPTCHA Workaround](#captcha-workaround) section for detailed instructions.

**Option 4: Two-Factor Authentication (2FA)**

If you have 2FA enabled on your TradingView account, you can authenticate automatically:

**Method A: TOTP Secret Key (Recommended)**

The most convenient method is to use your TOTP secret key, which allows automatic code generation:

```bash
# In your .env file or shell
export TV_USERNAME="your_username"
export TV_PASSWORD="your_password"
export TV_TOTP_SECRET="JBSWY3DPEHPK3PXP"  # Your TOTP secret key
```

```python
import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file

tv = TvDatafeed(
    username=os.getenv('TV_USERNAME'),
    password=os.getenv('TV_PASSWORD'),
    totp_secret=os.getenv('TV_TOTP_SECRET')
)
```

> **How to get your TOTP secret key:**
> 1. Go to TradingView Settings > Security > Two-factor authentication
> 2. When setting up 2FA, click "Can't scan?" to reveal the secret key
> 3. The key looks like: `JBSWY3DPEHPK3PXP` (base32 encoded)
> 4. Note: If 2FA is already set up, you may need to disable and re-enable it to see the secret

**Method B: Manual 2FA Code**

If you can't get the TOTP secret, you can provide the 6-digit code directly:

```python
tv = TvDatafeed(
    username='your_username',
    password='your_password',
    totp_code='123456'  # Current 6-digit code from your authenticator app
)
```

> **Note:** Manual codes expire every 30 seconds, so this method requires you to update the code each time you connect.

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

#### Date Range Search

**NEW in v1.4:** Instead of specifying `n_bars`, you can now fetch data by date range:

```python
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

# Get data for January 2024
df = tv.get_hist(
    'BTCUSDT',
    'BINANCE',
    Interval.in_1_hour,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)

# Get data for a specific week
df = tv.get_hist(
    'AAPL',
    'NASDAQ',
    Interval.in_daily,
    start_date=datetime(2024, 11, 1),
    end_date=datetime(2024, 11, 7)
)

# Access timezone metadata
print(f"Timezone: {df.attrs.get('timezone', 'Not set')}")
```

**Notes:**
- `start_date` and `end_date` are **mutually exclusive** with `n_bars`
- Both dates must be provided together
- Dates must be after 2000-01-01 and not in the future
- Timezone metadata is included in `df.attrs['timezone']`
- Supports both timezone-aware and naive datetime objects

#### Parameters

```python
tv.get_hist(
    symbol: str,                      # Symbol name
    exchange: str,                    # Exchange name
    interval: Interval,               # Time interval
    n_bars: int = None,               # Number of bars (max 5000) - mutually exclusive with date range
    fut_contract: int = None,         # Futures contract (1=front, 2=next)
    extended_session: bool = False,   # Include extended hours
    start_date: datetime = None,      # Start date (use with end_date) - NEW in v1.4
    end_date: datetime = None,        # End date (use with start_date) - NEW in v1.4
    timezone: str = None              # Timezone for datetime index - NEW in v1.5
) -> pd.DataFrame
```

#### Timezone Support (NEW in v1.5)

By default, timestamps are returned in your local system timezone. You can specify a timezone to get consistent datetime values:

```python
# Get data in UTC (recommended for cross-instrument analysis)
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=100, timezone='UTC')

# Get data in US Eastern time
df = tv.get_hist('AAPL', 'NASDAQ', Interval.in_daily, n_bars=50, timezone='America/New_York')

# Common timezones:
# - 'UTC': Coordinated Universal Time
# - 'America/New_York': US Eastern (EST/EDT)
# - 'America/Chicago': US Central (CST/CDT)
# - 'Europe/London': UK (GMT/BST)
# - 'Europe/Paris': Central European (CET/CEST)
# - 'Asia/Tokyo': Japan Standard Time
# - 'Asia/Hong_Kong': Hong Kong Time
```

You can also set the default timezone via environment variable:
```bash
export TV_TIMEZONE=UTC
```

The timezone is stored in DataFrame metadata:
```python
print(df.attrs.get('timezone'))  # Output: 'UTC'
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
TV_WS_TIMEOUT=5.0              # WebSocket per-message timeout (seconds)
TV_MAX_RESPONSE_TIME=60.0      # Maximum time to wait for complete response (seconds)

# Debug
TV_DEBUG=false

# Logging
TV_VERBOSE=true
```

### Using Configuration

```python
from tvDatafeed.config import TvDatafeedConfig

# Load from environment variables
config = TvDatafeedConfig.from_env()

# Or use defaults
config = TvDatafeedConfig.default()
```

### Verbose Logging

Control log verbosity to reduce noise in production:

#### Method 1: Parameter (Recommended)

```python
from tvDatafeed import TvDatafeed

# Quiet mode - only warnings and errors (production)
tv = TvDatafeed(verbose=False)

# Verbose mode - all info, warnings and errors (development/debugging)
tv = TvDatafeed(verbose=True)  # Default
```

#### Method 2: Environment Variable

```bash
# Set in .env file or shell
export TV_VERBOSE=false
```

```python
from tvDatafeed import TvDatafeed

# Will automatically use TV_VERBOSE from environment
tv = TvDatafeed()
```

#### Priority

When both parameter and environment variable are set, the **parameter takes priority**:

```bash
export TV_VERBOSE=true
```

```python
# This will use quiet mode despite TV_VERBOSE=true
tv = TvDatafeed(verbose=False)
```

#### What Gets Logged

**Verbose Mode (verbose=True)** - Default behavior:
- ✅ Info messages (authentication, connection, data retrieval progress)
- ✅ Warnings (non-critical issues, fallbacks)
- ✅ Errors (critical failures)
- ✅ Debug messages (if logging.DEBUG is set)

**Quiet Mode (verbose=False)** - Production use:
- ❌ Info messages suppressed
- ✅ Warnings shown
- ✅ Errors always shown
- ❌ Debug messages suppressed

#### Example: Clean Production Logs

```python
import logging
from tvDatafeed import TvDatafeed, Interval

# Configure root logger for production
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Create quiet TvDatafeed instance
tv = TvDatafeed(
    username='your_username',
    password='your_password',
    verbose=False  # Quiet mode
)

# Get data without noisy info logs
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=100)

# Only errors/warnings will be logged
```

#### Use Cases

**Use verbose=True (default) when:**
- Developing and debugging
- Learning the library
- Troubleshooting connection issues
- You want detailed progress information

**Use verbose=False when:**
- Running in production
- Scheduled/automated tasks
- Clean log output is important
- You only care about errors/warnings

**Note:** See [examples/quiet_mode.py](examples/quiet_mode.py) for a complete working example.

## 📝 Examples

Check out the [examples/](examples/) directory:

- **[basic_usage.py](examples/basic_usage.py)** - Getting started guide
- **[live_feed.py](examples/live_feed.py)** - Real-time data monitoring
- **[error_handling.py](examples/error_handling.py)** - Robust error handling
- **[2fa_authentication.py](examples/2fa_authentication.py)** - 🆕 Two-Factor Authentication (TOTP)
- **[date_range_search.py](examples/date_range_search.py)** - 🆕 Date Range Search (backtesting)
- **[quiet_mode.py](examples/quiet_mode.py)** - Verbose logging control
- **[captcha_workaround.py](examples/captcha_workaround.py)** - Handle CAPTCHA requirement
- **[symbol_format_guide.py](examples/symbol_format_guide.py)** - Symbol formatting guide

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

## 📌 Symbol Format Guide

Understanding the correct symbol format is crucial for reliable data retrieval.

### Format: EXCHANGE:SYMBOL

TradingView uses the format `EXCHANGE:SYMBOL` to uniquely identify instruments. While the library can work with just the symbol name, **using the full format is more reliable**.

#### ✅ Recommended (with exchange prefix)

```python
# Crypto
df = tv.get_hist('BINANCE:BTCUSDT', 'BINANCE', Interval.in_1_hour)

# Stocks
df = tv.get_hist('NASDAQ:AAPL', 'NASDAQ', Interval.in_daily)

# Futures
df = tv.get_hist('NSE:NIFTY', 'NSE', Interval.in_15_minute, fut_contract=1)
```

#### ⚠️ Alternative (symbol only)

```python
# Works but less reliable
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour)
```

### Finding the Correct Symbol Format

#### Method 1: Use search_symbol()

```python
from tvDatafeed import TvDatafeed

tv = TvDatafeed()

# Search for Bitcoin on Binance
results = tv.search_symbol('BTC', 'BINANCE')

# Display formatted results
print(tv.format_search_results(results))

# Use the first result
if results:
    exchange = results[0]['exchange']
    symbol = results[0]['symbol']
    full_symbol = f"{exchange}:{symbol}"

    df = tv.get_hist(full_symbol, exchange, Interval.in_1_hour, n_bars=100)
```

#### Method 2: Manual Search on TradingView

1. Go to [tradingview.com](https://www.tradingview.com)
2. Use the search bar to find your instrument
3. Look at the URL or chart title for the format
4. Example: Bitcoin on Binance shows as `BINANCE:BTCUSDT`

### Common Symbol Examples

**Cryptocurrency:**
```python
'BINANCE:BTCUSDT'   # Bitcoin/Tether on Binance
'COINBASE:BTCUSD'   # Bitcoin/USD on Coinbase
'BINANCE:ETHUSDT'   # Ethereum/Tether on Binance
'KRAKEN:BTCEUR'     # Bitcoin/Euro on Kraken
```

**US Stocks:**
```python
'NASDAQ:AAPL'       # Apple Inc.
'NYSE:TSLA'         # Tesla Inc.
'NASDAQ:GOOGL'      # Alphabet Inc.
'NYSE:JPM'          # JPMorgan Chase
```

**Indian Markets:**
```python
'NSE:NIFTY'         # Nifty 50 Index
'NSE:RELIANCE'      # Reliance Industries
'BSE:SENSEX'        # Sensex Index
```

**Forex:**
```python
'FX:EURUSD'         # Euro/US Dollar
'OANDA:GBPJPY'      # British Pound/Japanese Yen
```

**Commodities:**
```python
'MCX:CRUDEOIL'      # Crude Oil on MCX
'NYMEX:CL1!'        # WTI Crude Oil Futures
'COMEX:GC1!'        # Gold Futures
```

### Handling Timeout Issues

If you're experiencing timeout errors, you can increase the WebSocket timeout:

#### Method 1: Parameter (Recommended)

```python
from tvDatafeed import TvDatafeed

# Increase timeout to 30 seconds
tv = TvDatafeed(ws_timeout=30.0)

df = tv.get_hist('BINANCE:BTCUSDT', 'BINANCE', Interval.in_1_hour)
```

#### Method 2: Environment Variable

```bash
# Set in shell or .env file
export TV_WS_TIMEOUT=30.0
```

```python
# Will automatically use TV_WS_TIMEOUT
tv = TvDatafeed()
```

#### Method 3: NetworkConfig

```python
from tvDatafeed import TvDatafeed
from tvDatafeed.config import NetworkConfig

config = NetworkConfig(recv_timeout=30.0)
# Note: Currently NetworkConfig is read from environment
# Use TV_RECV_TIMEOUT environment variable instead
```

```bash
export TV_RECV_TIMEOUT=30.0
```

### Best Practices

1. **Always use EXCHANGE:SYMBOL format** when possible
2. **Use search_symbol()** to find correct symbol names
3. **Test with small n_bars** first (e.g., n_bars=10)
4. **Increase timeout** for slow connections or large data requests
5. **Enable debug logging** to see what's happening:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
tv = TvDatafeed()
tv.ws_debug = True  # See WebSocket messages
```

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
- 2FA enabled → Use `totp_secret` or `totp_code` parameter (see [2FA Authentication](#option-4-two-factor-authentication-2fa))
- Credentials not in environment variables
- CAPTCHA required (see below)

**Solution:**
```bash
export TV_USERNAME="your_username"
export TV_PASSWORD="your_password"
```

### reCAPTCHA / Rate Limit Issue (Common)

When trying to authenticate with username/password, you may see this error:

```
AuthenticationError: Authentication failed: You have been locked out. Please try again later.
```

**This is NOT a real rate limit** - it's TradingView's **invisible reCAPTCHA** blocking automated logins.

#### Why This Happens

TradingView uses Google reCAPTCHA v2 invisible on their login page. This reCAPTCHA:
- Runs automatically in the browser via JavaScript
- Validates that you're human before allowing login
- **Cannot be bypassed** by Python scripts (no JavaScript execution)

When reCAPTCHA validation fails (which it always does from scripts), TradingView returns a generic "rate_limit" error instead of a clear "reCAPTCHA required" message.

#### Solution: Use JWT Auth Token (Recommended)

Instead of username/password, extract your **JWT auth token** from the browser and use it directly.

##### Step 1: Get Your JWT Token

1. **Log in** to https://www.tradingview.com in your browser
2. **Open DevTools** (F12 or Ctrl+Shift+I)
3. **Go to Console** tab
4. **Type this command:**
   ```javascript
   window.user.auth_token
   ```
5. **Copy the token** - it looks like this:
   ```
   eyJhbGciOiJSUzUxMiIsImtpZCI6IkdaeFUiLCJ0eXAiOiJKV1QifQ.eyJ1c2VyX2lkIjo...
   ```

##### Step 2: Use the Token

**Method A: Environment Variable (Recommended)**

```bash
# In your .env file or shell
export TV_AUTH_TOKEN="eyJhbGciOiJSUzUxMiIs..."
```

```python
import os
from tvDatafeed import TvDatafeed

tv = TvDatafeed(auth_token=os.getenv('TV_AUTH_TOKEN'))

# Now you can fetch data with full Pro/Premium access
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=5000)
```

**Method B: Direct Usage (Testing Only)**

```python
from tvDatafeed import TvDatafeed

tv = TvDatafeed(auth_token='eyJhbGciOiJSUzUxMiIs...')
```

##### Alternative: Via Network Tab

If `window.user.auth_token` doesn't work:

1. **Open DevTools** > **Network** tab
2. **Filter by "WS"** (WebSocket)
3. **Refresh the page** or open a chart
4. **Click on the WebSocket connection** to `wss://data.tradingview.com`
5. **Go to "Messages" tab**
6. **Look for** `set_auth_token` message - copy the token value

#### Important Notes

| Aspect | Details |
|--------|---------|
| **Token Type** | JWT (JSON Web Token) - starts with `eyJ` |
| **NOT the sessionid** | The `sessionid` cookie does NOT work for WebSocket auth |
| **Expiration** | Tokens expire (usually 4-24 hours). Extract a new one when needed |
| **Security** | Treat like a password - never commit to git |
| **Plan Features** | Token includes your subscription (Pro, Premium, etc.) |

#### Why Username/Password Doesn't Work

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Your Script   │────▶│   TradingView    │────▶│   reCAPTCHA    │
│  (Python/HTTP)  │     │   Login Page     │     │   (Invisible)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                                 ┌─────────────────┐
                                                 │  JavaScript     │
                                                 │  Validation     │
                                                 │  (Not in Python)│
                                                 └─────────────────┘
                                                         │
                                                         ▼
                                                 ┌─────────────────┐
                                                 │  ❌ FAILS       │
                                                 │  "rate_limit"   │
                                                 └─────────────────┘
```

The script cannot execute JavaScript, so reCAPTCHA always fails, returning a misleading "rate_limit" error.

### CAPTCHA Workaround (Legacy)

> **Note:** This section is kept for backward compatibility. The [reCAPTCHA solution above](#recaptcha--rate-limit-issue-common) is the recommended approach.

If you see `CaptchaRequiredError`, follow the JWT token extraction method above.

#### Complete Example

See [examples/captcha_workaround.py](examples/captcha_workaround.py) for a complete working example with error handling:

```bash
python examples/captcha_workaround.py
```

#### Token Storage Best Practices

- ⏱️ **Token Expiration:** Tokens expire after some time. Extract a new one if needed.
- 🔒 **Security:** Treat your token like a password. Never commit it to version control.
- 🔄 **Session-tied:** Token is tied to your TradingView session.
- 📝 **Storage:** Store in environment variables or secure configuration files.

#### Automated Token Retrieval (Server Scripts)

For automated/scheduled scripts running on servers, you can use the token management utilities:

##### Installation

```bash
pip install playwright playwright-stealth pyotp
playwright install chromium
```

##### Setup

1. Configure your `.env` file:
```bash
TV_USERNAME=your_username
TV_PASSWORD=your_password
TV_TOTP_SECRET=your_totp_secret  # Optional, for 2FA accounts
```

2. Extract token (first time or when expired):
```bash
python scripts/get_auth_token.py
```

##### Usage in Your Scripts

```python
from scripts.token_manager import get_valid_token, get_token_info
from tvDatafeed import TvDatafeed, Interval

# Get valid token (auto-refreshes if expired)
token = get_valid_token(auto_refresh=True)

if token:
    # Check token info
    info = get_token_info(token)
    print(f"Plan: {info['plan']}, Expires: {info['expires_at']}")

    # Use with TvDatafeed
    tv = TvDatafeed(auth_token=token)
    df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, 100)
```

##### Token Manager Features

- **Priority**: Environment variable > Cache file > Auto-refresh
- **Validation**: Checks expiration with configurable threshold (default: 1 hour before expiry)
- **Caching**: Stores token in `.token_cache.json` with secure permissions
- **Auto-refresh**: Uses Playwright + stealth mode to get fresh token

See [examples/automated_data_fetch.py](examples/automated_data_fetch.py) for a complete server script example.

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
