# Live Data Feed Examples

This guide shows how to use `TvDatafeedLive` for real-time data monitoring.

## Basic Live Feed

### Simple Callback

```python
from tvDatafeed import TvDatafeedLive, Interval
import time

def on_new_data(seis, data):
    """Called when new bar is available."""
    close = data['close'].iloc[0]
    volume = data['volume'].iloc[0]
    print(f"[{seis.symbol}] Close: ${close:,.2f}, Volume: {volume:,.0f}")

# Create live feed
tv = TvDatafeedLive()

try:
    # Add symbol to monitor
    seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)

    # Add callback
    consumer = tv.new_consumer(seis, on_new_data)

    print(f"Monitoring {seis.symbol}... Press Ctrl+C to stop")

    # Keep running
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    # Always cleanup
    tv.del_tvdatafeed()
    print("Done")
```

## Multiple Symbols

### Monitor Multiple Assets

```python
from tvDatafeed import TvDatafeedLive, Interval
import time

def create_handler(name):
    """Create a handler with custom name for logging."""
    def handler(seis, data):
        close = data['close'].iloc[0]
        change = data['close'].iloc[0] - data['open'].iloc[0]
        pct = (change / data['open'].iloc[0]) * 100
        print(f"[{name}] ${close:,.2f} ({pct:+.2f}%)")
    return handler

tv = TvDatafeedLive()

try:
    # Define symbols to monitor
    symbols = [
        ('BTCUSDT', 'BINANCE', 'BTC'),
        ('ETHUSDT', 'BINANCE', 'ETH'),
        ('SOLUSDT', 'BINANCE', 'SOL'),
    ]

    # Add each symbol
    seises = []
    consumers = []

    for symbol, exchange, name in symbols:
        seis = tv.new_seis(symbol, exchange, Interval.in_1_minute)
        consumer = tv.new_consumer(seis, create_handler(name))
        seises.append(seis)
        consumers.append(consumer)
        print(f"Added {name}")

    print("\nMonitoring... Press Ctrl+C to stop\n")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    tv.del_tvdatafeed()
    print("Done")
```

## Multiple Callbacks per Symbol

### Different Processing for Same Data

```python
from tvDatafeed import TvDatafeedLive, Interval
import time
import logging

logging.basicConfig(level=logging.INFO)

def log_to_console(seis, data):
    """Log to console."""
    print(f"[{seis.symbol}] {data.index[0]}: ${data['close'].iloc[0]:,.2f}")

def check_alerts(seis, data):
    """Check for price alerts."""
    close = data['close'].iloc[0]

    # Example alerts
    if close > 70000:
        print(f"*** ALERT: {seis.symbol} above $70,000! ***")
    elif close < 60000:
        print(f"*** ALERT: {seis.symbol} below $60,000! ***")

def calculate_indicators(seis, data):
    """Calculate technical indicators."""
    # This is simplified - in production, you'd maintain history
    print(f"[{seis.symbol}] Processing for indicators...")

tv = TvDatafeedLive()

try:
    seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)

    # Multiple consumers for same seis
    consumer1 = tv.new_consumer(seis, log_to_console)
    consumer2 = tv.new_consumer(seis, check_alerts)
    consumer3 = tv.new_consumer(seis, calculate_indicators)

    print("Monitoring with 3 callbacks... Press Ctrl+C to stop")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    pass

finally:
    tv.del_tvdatafeed()
```

## Data Accumulation

### Build Historical Data

```python
from tvDatafeed import TvDatafeedLive, Interval
import pandas as pd
import time
import threading

class DataAccumulator:
    """Accumulate live data into a DataFrame."""

    def __init__(self, max_rows=1000):
        self.data = pd.DataFrame()
        self.max_rows = max_rows
        self.lock = threading.Lock()

    def callback(self, seis, data):
        """Callback to accumulate data."""
        with self.lock:
            self.data = pd.concat([self.data, data])

            # Keep only last max_rows
            if len(self.data) > self.max_rows:
                self.data = self.data.iloc[-self.max_rows:]

    def get_data(self):
        """Get accumulated data (thread-safe)."""
        with self.lock:
            return self.data.copy()

# Create accumulator
accumulator = DataAccumulator(max_rows=100)

tv = TvDatafeedLive()

try:
    seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)
    consumer = tv.new_consumer(seis, accumulator.callback)

    print("Accumulating data... Press Ctrl+C to stop")

    while True:
        time.sleep(10)  # Check every 10 seconds
        df = accumulator.get_data()
        if len(df) > 0:
            print(f"\n--- Accumulated {len(df)} bars ---")
            print(f"Latest: {df.iloc[-1]['close']:.2f}")
            print(f"High: {df['high'].max():.2f}")
            print(f"Low: {df['low'].min():.2f}")

except KeyboardInterrupt:
    pass

finally:
    tv.del_tvdatafeed()

    # Final data
    final_df = accumulator.get_data()
    print(f"\nFinal dataset: {len(final_df)} bars")
    print(final_df.tail())
```

## Fetching Historical Data While Live

### Combined Usage

```python
from tvDatafeed import TvDatafeedLive, Interval
import time

def on_new_data(seis, data):
    print(f"[LIVE] {seis.symbol}: ${data['close'].iloc[0]:,.2f}")

tv = TvDatafeedLive()

try:
    # Start live monitoring
    seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)
    consumer = tv.new_consumer(seis, on_new_data)

    print("Live feed started")

    # Can still fetch historical data while live feed is running
    print("\nFetching historical data...")
    df_hourly = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=24)
    print(f"Got {len(df_hourly)} hourly bars")

    df_daily = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=30)
    print(f"Got {len(df_daily)} daily bars")

    print("\nHistorical + Live data working together!")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    pass

finally:
    tv.del_tvdatafeed()
```

## Error Handling in Callbacks

### Safe Callback Pattern

```python
from tvDatafeed import TvDatafeedLive, Interval
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_callback(seis, data):
    """Callback with error handling."""
    try:
        # Your logic here
        close = data['close'].iloc[0]

        # Simulate potential error
        if close > 70000:
            # Do something that might fail
            result = process_data(data)
            save_to_database(result)

        print(f"[{seis.symbol}] Processed: ${close:,.2f}")

    except Exception as e:
        # Log error but don't crash
        logger.error(f"Error in callback for {seis.symbol}: {e}")
        # Optionally send alert
        # send_alert(f"Callback error: {e}")

def process_data(data):
    """Process data (may raise exception)."""
    return data

def save_to_database(data):
    """Save to database (may raise exception)."""
    pass

tv = TvDatafeedLive()

try:
    seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)
    consumer = tv.new_consumer(seis, safe_callback)

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    pass

finally:
    tv.del_tvdatafeed()
```

## Using Timeouts

### Non-Blocking Operations

```python
from tvDatafeed import TvDatafeedLive, Interval
import time

tv = TvDatafeedLive()

def my_callback(seis, data):
    print(f"New data: {data['close'].iloc[0]}")

try:
    # With 5-second timeout
    seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute, timeout=5)

    if seis is False:
        print("Failed to create seis within 5 seconds")
    else:
        consumer = tv.new_consumer(seis, my_callback, timeout=5)

        if consumer is False:
            print("Failed to create consumer within 5 seconds")
        else:
            print("Success!")

            while True:
                time.sleep(1)

except KeyboardInterrupt:
    pass

finally:
    tv.del_tvdatafeed()
```

## Cleanup Patterns

### Removing Individual Components

```python
from tvDatafeed import TvDatafeedLive, Interval
import time

tv = TvDatafeedLive()

def callback(seis, data):
    print(f"{seis.symbol}: ${data['close'].iloc[0]:,.2f}")

try:
    # Create
    seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)
    consumer = tv.new_consumer(seis, callback)

    time.sleep(30)  # Monitor for 30 seconds

    # Remove just the consumer (seis keeps running)
    tv.del_consumer(consumer)
    print("Consumer removed")

    time.sleep(10)

    # Remove the seis (stops all monitoring for this symbol)
    tv.del_seis(seis)
    print("Seis removed")

except KeyboardInterrupt:
    pass

finally:
    # Full cleanup
    tv.del_tvdatafeed()
```

### Using Seis Methods

```python
from tvDatafeed import TvDatafeedLive, Interval
import time

tv = TvDatafeedLive()

def callback(seis, data):
    print(f"{seis.symbol}: ${data['close'].iloc[0]:,.2f}")

try:
    seis = tv.new_seis('BTCUSDT', 'BINANCE', Interval.in_1_minute)

    # Create consumer via seis
    consumer = seis.new_consumer(callback)

    time.sleep(30)

    # Get historical data via seis
    df = seis.get_hist(n_bars=100)
    print(f"Historical: {len(df)} bars")

    # Remove consumer via seis
    seis.del_consumer(consumer)

    # Remove seis via seis
    seis.del_seis()

except KeyboardInterrupt:
    pass

finally:
    tv.del_tvdatafeed()
```
