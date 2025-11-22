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
- Check if 2FA is enabled (not yet supported in these examples)
- Ensure credentials are set in environment variables

**"Timeout errors"**
- Check your internet connection
- TradingView might be experiencing issues
- Try again later

## More Information

For more details, see the main [README.md](../README.md) in the project root.
