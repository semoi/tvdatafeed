# TvDatafeed Examples

This directory contains example scripts demonstrating how to use TvDatafeed.

## Prerequisites

1. Install TvDatafeed:
```bash
pip install -e ..
```

2. (Optional) Set up environment variables for authentication:
```bash
export TV_USERNAME="your_username"
export TV_PASSWORD="your_password"
```

Or create a `.env` file in the project root:
```
TV_USERNAME=your_username
TV_PASSWORD=your_password
```

## Examples

### 1. Basic Usage (`basic_usage.py`)

Demonstrates fundamental features:
- Connecting to TradingView (with and without authentication)
- Downloading historical data
- Working with DataFrame results
- Basic data analysis
- Saving data to CSV

**Run:**
```bash
python basic_usage.py
```

**What you'll learn:**
- How to initialize TvDatafeed
- How to fetch historical bars
- How to work with the returned DataFrame
- Basic data manipulation with pandas

---

### 2. Live Feed (`live_feed.py`)

Shows how to use real-time data monitoring:
- Creating live data feeds for multiple symbols
- Setting up callbacks for new data
- Multiple consumers for the same symbol
- Proper cleanup

**Run:**
```bash
python live_feed.py
```

**Requirements:**
- TradingView account credentials (authenticated access required)

**What you'll learn:**
- How to create SEIS (Symbol-Exchange-Interval Set)
- How to register callbacks
- How to monitor multiple symbols simultaneously
- How to properly clean up resources

---

### 3. Error Handling (`error_handling.py`)

Demonstrates robust error handling:
- Authentication errors
- Invalid symbols
- Timeout handling
- Symbol search

**Run:**
```bash
python error_handling.py
```

**What you'll learn:**
- How to handle different types of errors
- How to use symbol search to find correct symbol names
- Best practices for error handling
- How to use logging for debugging

---

### 4. Two-Factor Authentication (`2fa_authentication.py`) 🆕

Demonstrates 2FA/TOTP authentication (NEW in PR #30):
- TOTP secret key for automatic code generation (recommended)
- Manual 6-digit code input
- Environment variable configuration
- Production-ready security patterns

**Run:**
```bash
python 2fa_authentication.py
```

**Requirements:**
- TradingView account with 2FA enabled
- TOTP secret key (from TradingView 2FA setup)
- Optional: `pyotp` package for automatic code generation

**What you'll learn:**
- How to authenticate with 2FA/TOTP
- How to get your TOTP secret key from TradingView
- Secure credential management with environment variables
- Error handling for 2FA scenarios

---

### 5. Date Range Search (`date_range_search.py`) 🆕

Demonstrates fetching data by date range instead of n_bars (NEW in PR #69):
- Query by start_date and end_date
- Timezone-aware data handling
- Validation of date ranges
- Use cases for backtesting

**Run:**
```bash
python date_range_search.py
```

**What you'll learn:**
- How to use start_date and end_date parameters
- Difference between n_bars and date range queries
- How to access timezone metadata in DataFrame
- Date validation rules and constraints

---

### 6. Quiet Mode (`quiet_mode.py`) 🆕

Demonstrates verbose logging control (NEW in PR #37):
- Quiet mode for production (verbose=False)
- Verbose mode for development (verbose=True)
- Environment variable configuration (TV_VERBOSE)
- Logging level control

**Run:**
```bash
python quiet_mode.py
```

**What you'll learn:**
- How to control log verbosity
- Difference between verbose and quiet modes
- Production vs development logging patterns

---

### 7. CAPTCHA Workaround (`captcha_workaround.py`)

Demonstrates handling CAPTCHA authentication requirements:
- Extracting auth token from browser
- Using pre-obtained tokens
- Secure token storage

**Run:**
```bash
python captcha_workaround.py
```

**What you'll learn:**
- How to handle CaptchaRequiredError
- How to extract auth token from browser cookies
- Secure token management

---

### 8. Symbol Format Guide (`symbol_format_guide.py`)

Comprehensive guide for symbol formatting:
- EXCHANGE:SYMBOL format
- Symbol search usage
- Common exchange symbols
- Troubleshooting symbol issues

**Run:**
```bash
python symbol_format_guide.py
```

**What you'll learn:**
- Correct symbol format for TradingView
- How to find symbols for different markets
- Best practices for symbol usage

---

## Tips

### Authentication

For examples requiring authentication, you can:

**Option 1: Environment variables (recommended)**
```bash
export TV_USERNAME="your_username"
export TV_PASSWORD="your_password"
python live_feed.py
```

**Option 2: .env file**
Create a `.env` file in the project root:
```
TV_USERNAME=your_username
TV_PASSWORD=your_password
```

**Option 3: Direct in code (not recommended for production)**
```python
tv = TvDatafeed(username="your_username", password="your_password")
```

### Finding Symbol Names

If you're unsure of the exact symbol name, use symbol search:

```python
from tvDatafeed import TvDatafeed

tv = TvDatafeed()
results = tv.search_symbol('BTC', 'BINANCE')

for result in results:
    print(f"{result['symbol']} - {result['description']}")
```

### Supported Intervals

```python
from tvDatafeed import Interval

# Minutes
Interval.in_1_minute
Interval.in_3_minute
Interval.in_5_minute
Interval.in_15_minute
Interval.in_30_minute
Interval.in_45_minute

# Hours
Interval.in_1_hour
Interval.in_2_hour
Interval.in_3_hour
Interval.in_4_hour

# Other
Interval.in_daily
Interval.in_weekly
Interval.in_monthly
```

### Common Exchanges

- Crypto: `BINANCE`, `COINBASE`, `KRAKEN`, `BITFINEX`
- US Stocks: `NASDAQ`, `NYSE`, `AMEX`
- Indian Markets: `NSE`, `BSE`
- Commodities: `MCX`, `NYMEX`, `COMEX`
- Forex: `FX`, `OANDA`

### Troubleshooting

**"No data returned"**
- Check symbol name with `search_symbol()`
- Verify exchange is correct
- Try with authentication

**"Authentication failed"**
- Verify username and password
- If 2FA is enabled, see `2fa_authentication.py` for setup instructions
- Ensure credentials are set in environment variables
- For CAPTCHA issues, see `captcha_workaround.py`

**"TwoFactorRequiredError"**
- Your account has 2FA enabled
- Provide `totp_secret` (recommended) or `totp_code` parameter
- See `2fa_authentication.py` for detailed examples

**"Timeout errors"**
- Check your internet connection
- Increase timeout: `TvDatafeed(ws_timeout=30.0)`
- TradingView might be experiencing issues
- Try again later

## More Information

For more details, see the main [README.md](../README.md) in the project root.
