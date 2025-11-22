"""
Date Range Search Example

This example demonstrates how to use the date range search feature
(introduced in v1.4) to fetch historical data by specifying start and
end dates instead of number of bars.

Requirements:
- TvDatafeed v1.4+
- No authentication required for basic usage (but recommended)

Features demonstrated:
- Fetching data by date range
- Using timezone-aware datetimes
- Comparing with traditional n_bars method
- Accessing timezone metadata
- Error handling for invalid date ranges
"""

import os
import sys
from datetime import datetime, timedelta
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tvDatafeed import TvDatafeed, Interval

def example_basic_date_range():
    """Example 1: Basic date range query"""
    print("=" * 60)
    print("Example 1: Basic Date Range Query")
    print("=" * 60)

    tv = TvDatafeed()

    # Get Bitcoin data for January 2024 on 1-hour interval
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)

    print(f"Fetching BTCUSDT data from {start_date.date()} to {end_date.date()}")

    df = tv.get_hist(
        'BTCUSDT',
        'BINANCE',
        Interval.in_1_hour,
        start_date=start_date,
        end_date=end_date
    )

    if df is not None:
        print(f"\nData retrieved: {len(df)} rows")
        print(f"Date range: {df.index[0]} to {df.index[-1]}")
        print(f"Timezone: {df.attrs.get('timezone', 'Not set')}")
        print("\nFirst 5 rows:")
        print(df.head())
    else:
        print("No data retrieved")


def example_specific_week():
    """Example 2: Get data for a specific week"""
    print("\n" + "=" * 60)
    print("Example 2: Specific Week Query")
    print("=" * 60)

    tv = TvDatafeed()

    # Get AAPL data for first week of November 2024
    start_date = datetime(2024, 11, 1)
    end_date = datetime(2024, 11, 7)

    print(f"Fetching AAPL data from {start_date.date()} to {end_date.date()}")

    df = tv.get_hist(
        'AAPL',
        'NASDAQ',
        Interval.in_daily,
        start_date=start_date,
        end_date=end_date
    )

    if df is not None:
        print(f"\nData retrieved: {len(df)} rows")
        print("\nAll data:")
        print(df)
    else:
        print("No data retrieved")


def example_comparison_with_n_bars():
    """Example 3: Compare date range with n_bars approach"""
    print("\n" + "=" * 60)
    print("Example 3: Comparison with n_bars Method")
    print("=" * 60)

    tv = TvDatafeed()

    # Method 1: Using date range
    start_date = datetime(2024, 11, 1)
    end_date = datetime(2024, 11, 15)

    print(f"Method 1: Date range ({start_date.date()} to {end_date.date()})")
    df_date_range = tv.get_hist(
        'BTCUSDT',
        'BINANCE',
        Interval.in_daily,
        start_date=start_date,
        end_date=end_date
    )

    if df_date_range is not None:
        print(f"  - Retrieved {len(df_date_range)} bars")
        print(f"  - First bar: {df_date_range.index[0]}")
        print(f"  - Last bar: {df_date_range.index[-1]}")

    # Method 2: Using n_bars
    print(f"\nMethod 2: n_bars (last 15 bars)")
    df_n_bars = tv.get_hist(
        'BTCUSDT',
        'BINANCE',
        Interval.in_daily,
        n_bars=15
    )

    if df_n_bars is not None:
        print(f"  - Retrieved {len(df_n_bars)} bars")
        print(f"  - First bar: {df_n_bars.index[0]}")
        print(f"  - Last bar: {df_n_bars.index[-1]}")

    print("\nComparison:")
    print("  - Date range: Precise control over time period")
    print("  - n_bars: Always gets most recent data")


def example_error_handling():
    """Example 4: Error handling for invalid date ranges"""
    print("\n" + "=" * 60)
    print("Example 4: Error Handling")
    print("=" * 60)

    tv = TvDatafeed()

    # Error 1: Start date after end date
    print("Test 1: Start date after end date")
    try:
        df = tv.get_hist(
            'BTCUSDT',
            'BINANCE',
            Interval.in_1_hour,
            start_date=datetime(2024, 1, 31),
            end_date=datetime(2024, 1, 1)
        )
        print("  - Unexpected success!")
    except Exception as e:
        print(f"  - Correctly caught error: {type(e).__name__}")

    # Error 2: Future dates
    print("\nTest 2: Future dates")
    try:
        future_date = datetime.now() + timedelta(days=30)
        df = tv.get_hist(
            'BTCUSDT',
            'BINANCE',
            Interval.in_1_hour,
            start_date=datetime(2024, 1, 1),
            end_date=future_date
        )
        print("  - Unexpected success!")
    except Exception as e:
        print(f"  - Correctly caught error: {type(e).__name__}")

    # Error 3: Dates before 2000
    print("\nTest 3: Dates before 2000 (TradingView limitation)")
    try:
        df = tv.get_hist(
            'BTCUSDT',
            'BINANCE',
            Interval.in_1_hour,
            start_date=datetime(1999, 1, 1),
            end_date=datetime(1999, 12, 31)
        )
        print("  - Unexpected success!")
    except Exception as e:
        print(f"  - Correctly caught error: {type(e).__name__}")

    # Error 4: Mixing n_bars with date range
    print("\nTest 4: Mixing n_bars with date range (mutually exclusive)")
    try:
        df = tv.get_hist(
            'BTCUSDT',
            'BINANCE',
            Interval.in_1_hour,
            n_bars=100,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        print("  - Unexpected success!")
    except Exception as e:
        print(f"  - Correctly caught error: {type(e).__name__}")

    # Error 5: Only providing start_date
    print("\nTest 5: Only providing start_date (must provide both)")
    try:
        df = tv.get_hist(
            'BTCUSDT',
            'BINANCE',
            Interval.in_1_hour,
            start_date=datetime(2024, 1, 1)
        )
        print("  - Unexpected success!")
    except Exception as e:
        print(f"  - Correctly caught error: {type(e).__name__}")


def example_timezone_metadata():
    """Example 5: Working with timezone metadata"""
    print("\n" + "=" * 60)
    print("Example 5: Timezone Metadata")
    print("=" * 60)

    tv = TvDatafeed()

    # Get data with date range (includes timezone metadata)
    df_with_tz = tv.get_hist(
        'BTCUSDT',
        'BINANCE',
        Interval.in_1_hour,
        start_date=datetime(2024, 11, 1),
        end_date=datetime(2024, 11, 7)
    )

    # Get data with n_bars (no timezone metadata)
    df_without_tz = tv.get_hist(
        'BTCUSDT',
        'BINANCE',
        Interval.in_1_hour,
        n_bars=100
    )

    print("With date range:")
    if df_with_tz is not None:
        tz = df_with_tz.attrs.get('timezone', 'Not set')
        print(f"  - Timezone: {tz}")
        print(f"  - Has timezone metadata: {tz != 'Not set'}")

    print("\nWith n_bars (traditional):")
    if df_without_tz is not None:
        tz = df_without_tz.attrs.get('timezone', 'Not set')
        print(f"  - Timezone: {tz}")
        print(f"  - Has timezone metadata: {tz != 'Not set'}")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("TvDatafeed Date Range Search Examples")
    print("=" * 60)
    print("\nThese examples demonstrate the new date range search feature")
    print("introduced in TvDatafeed v1.4.")
    print("\nNote: Some examples may fail if you don't have network access")
    print("or if TradingView's API is unavailable.\n")

    try:
        # Run examples
        example_basic_date_range()
        example_specific_week()
        example_comparison_with_n_bars()
        example_error_handling()
        example_timezone_metadata()

        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
