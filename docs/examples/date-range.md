# Date Range Query Examples

This guide shows how to fetch historical data for specific date ranges.

## Basic Date Range Query

### Simple Example

```python
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

# Get data for January 2024
df = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_1_hour,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)

print(f"Got {len(df)} bars from {df.index[0]} to {df.index[-1]}")
print(df.head())
```

## Date Range vs n_bars

### When to Use Each

```python
from datetime import datetime, timedelta
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

# Use n_bars when you need a specific number of recent bars
df_nbars = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_daily,
    n_bars=100  # Last 100 bars
)
print(f"n_bars: {len(df_nbars)} bars")

# Use date range when you need a specific time period
df_range = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_daily,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 3, 31)
)
print(f"Date range: {len(df_range)} bars")
```

!!! warning "Mutually Exclusive"
    You cannot use both `n_bars` and date range. Choose one or the other.

## Dynamic Date Ranges

### Last N Days

```python
from datetime import datetime, timedelta
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

# Last 7 days
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

df = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_1_hour,
    start_date=start_date,
    end_date=end_date
)

print(f"Last 7 days: {len(df)} hourly bars")
```

### Last N Months

```python
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

# Last 3 months
end_date = datetime.now()
start_date = end_date - relativedelta(months=3)

df = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_daily,
    start_date=start_date,
    end_date=end_date
)

print(f"Last 3 months: {len(df)} daily bars")
```

### Year to Date

```python
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

# YTD (Year to Date)
year = datetime.now().year
start_date = datetime(year, 1, 1)
end_date = datetime.now()

df = tv.get_hist(
    symbol='AAPL',
    exchange='NASDAQ',
    interval=Interval.in_daily,
    start_date=start_date,
    end_date=end_date
)

print(f"YTD {year}: {len(df)} daily bars")
```

## Working with Different Timeframes

### Intraday Data

```python
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

# Get 1-minute data for a single day
df = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_1_minute,
    start_date=datetime(2024, 1, 15, 0, 0),
    end_date=datetime(2024, 1, 15, 23, 59)
)

print(f"1-minute bars for Jan 15: {len(df)} bars")
print(f"Expected: ~1440 bars (24 hours * 60 minutes)")
```

### Hourly Data

```python
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

# Get hourly data for a week
df = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_1_hour,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 7)
)

print(f"Hourly bars for first week: {len(df)} bars")
print(f"Expected: ~168 bars (7 days * 24 hours)")
```

## Date Range Validation

### Valid Date Range

```python
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval
from tvDatafeed.exceptions import DataValidationError

tv = TvDatafeed()

# Check validity before querying
start = datetime(2024, 1, 1)
end = datetime(2024, 1, 31)

if tv.is_valid_date_range(start, end):
    df = tv.get_hist(
        symbol='BTCUSDT',
        exchange='BINANCE',
        interval=Interval.in_daily,
        start_date=start,
        end_date=end
    )
    print(f"Got {len(df)} bars")
else:
    print("Invalid date range!")
```

### Handling Validation Errors

```python
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval
from tvDatafeed.exceptions import DataValidationError

tv = TvDatafeed()

try:
    # Invalid: start > end
    df = tv.get_hist(
        symbol='BTCUSDT',
        exchange='BINANCE',
        interval=Interval.in_daily,
        start_date=datetime(2024, 12, 31),
        end_date=datetime(2024, 1, 1)  # Before start!
    )
except DataValidationError as e:
    print(f"Validation error: {e}")
    print(f"Field: {e.field}")
    print(f"Value: {e.value}")
    print(f"Reason: {e.reason}")
```

## Timezone Handling

### Timezone Metadata

```python
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

df = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_1_hour,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 7)
)

# Access timezone metadata
timezone = df.attrs.get('timezone', 'Not set')
print(f"Timezone: {timezone}")
```

### Working with pytz

```python
from datetime import datetime
import pytz
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

# Create timezone-aware datetimes
eastern = pytz.timezone('US/Eastern')
start = eastern.localize(datetime(2024, 1, 1, 9, 30))  # Market open
end = eastern.localize(datetime(2024, 1, 5, 16, 0))    # Market close

# Convert to UTC for API
start_utc = start.astimezone(pytz.UTC).replace(tzinfo=None)
end_utc = end.astimezone(pytz.UTC).replace(tzinfo=None)

df = tv.get_hist(
    symbol='AAPL',
    exchange='NASDAQ',
    interval=Interval.in_15_minute,
    start_date=start_utc,
    end_date=end_utc
)

print(f"Got {len(df)} bars")
```

## Batch Queries

### Multiple Date Ranges

```python
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tvDatafeed import TvDatafeed, Interval
import pandas as pd

tv = TvDatafeed()

# Get data for each quarter of 2023
quarters = [
    (datetime(2023, 1, 1), datetime(2023, 3, 31), "Q1"),
    (datetime(2023, 4, 1), datetime(2023, 6, 30), "Q2"),
    (datetime(2023, 7, 1), datetime(2023, 9, 30), "Q3"),
    (datetime(2023, 10, 1), datetime(2023, 12, 31), "Q4"),
]

all_data = []

for start, end, name in quarters:
    df = tv.get_hist(
        symbol='BTCUSDT',
        exchange='BINANCE',
        interval=Interval.in_daily,
        start_date=start,
        end_date=end
    )
    df['quarter'] = name
    all_data.append(df)
    print(f"{name}: {len(df)} bars")

# Combine all quarters
full_year = pd.concat(all_data)
print(f"\nTotal 2023: {len(full_year)} bars")
```

### Monthly Data Collection

```python
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tvDatafeed import TvDatafeed, Interval
import pandas as pd

tv = TvDatafeed()

# Collect monthly data for a year
start_month = datetime(2023, 1, 1)
all_data = []

for i in range(12):
    month_start = start_month + relativedelta(months=i)
    month_end = month_start + relativedelta(months=1) - relativedelta(days=1)

    df = tv.get_hist(
        symbol='AAPL',
        exchange='NASDAQ',
        interval=Interval.in_daily,
        start_date=month_start,
        end_date=month_end
    )

    all_data.append(df)
    print(f"{month_start.strftime('%B %Y')}: {len(df)} bars")

# Combine
full_year = pd.concat(all_data)
full_year = full_year[~full_year.index.duplicated()]  # Remove duplicates
print(f"\nTotal: {len(full_year)} bars")
```

## Analysis Examples

### Compare Periods

```python
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

# Compare Q1 2023 vs Q1 2024
q1_2023 = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_daily,
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 3, 31)
)

q1_2024 = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_daily,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 3, 31)
)

# Calculate returns
ret_2023 = (q1_2023['close'].iloc[-1] / q1_2023['close'].iloc[0] - 1) * 100
ret_2024 = (q1_2024['close'].iloc[-1] / q1_2024['close'].iloc[0] - 1) * 100

print("Q1 Performance Comparison:")
print(f"  2023: {ret_2023:+.2f}%")
print(f"  2024: {ret_2024:+.2f}%")
```

### Specific Event Analysis

```python
from datetime import datetime, timedelta
from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

# Analyze price action around Bitcoin halving (approx April 2024)
event_date = datetime(2024, 4, 20)
days_before = 30
days_after = 30

df = tv.get_hist(
    symbol='BTCUSDT',
    exchange='BINANCE',
    interval=Interval.in_daily,
    start_date=event_date - timedelta(days=days_before),
    end_date=event_date + timedelta(days=days_after)
)

# Find event position
event_idx = df.index.get_indexer([event_date], method='nearest')[0]

# Before event
before = df.iloc[:event_idx]
# After event
after = df.iloc[event_idx:]

print("Halving Analysis:")
print(f"  30 days before: ${before['close'].iloc[0]:,.0f} -> ${before['close'].iloc[-1]:,.0f}")
print(f"  30 days after: ${after['close'].iloc[0]:,.0f} -> ${after['close'].iloc[-1]:,.0f}")
```
