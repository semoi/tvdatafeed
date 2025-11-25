"""
Basic usage example for TvDatafeed

This example demonstrates:
- Connecting to TradingView
- Downloading historical data
- Working with the DataFrame result

✅ NEW in v2.0: HTTP authentication automatically bypasses reCAPTCHA!
Simply use username/password - no manual token extraction needed.
"""
import os
from tvDatafeed import TvDatafeed, Interval
import pandas as pd


def main():
    """Main example function"""
    print("=" * 60)
    print("TvDatafeed - Basic Usage Example")
    print("=" * 60)

    # Method 1: No authentication (limited access)
    print("\n1. Connecting without authentication (limited access)...")
    tv = TvDatafeed()
    print("   ✓ Connected (no-login mode)")

    # Method 2: With authentication (recommended for full access)
    # ✅ NEW in v2.0: HTTP auth bypasses reCAPTCHA automatically!
    # Uncomment below to use with credentials:
    # tv = TvDatafeed(
    #     username=os.getenv('TV_USERNAME'),
    #     password=os.getenv('TV_PASSWORD'),
    #     totp_secret=os.getenv('TV_TOTP_SECRET')  # If 2FA enabled
    # )
    # No more CAPTCHA errors!

    # Download Bitcoin data
    print("\n2. Downloading BTCUSDT data from Binance...")
    symbol = 'BTCUSDT'
    exchange = 'BINANCE'
    interval = Interval.in_1_hour
    n_bars = 100

    df = tv.get_hist(
        symbol=symbol,
        exchange=exchange,
        interval=interval,
        n_bars=n_bars
    )

    if df is not None and not df.empty:
        print(f"   ✓ Downloaded {len(df)} bars")

        # Display data summary
        print("\n3. Data Summary:")
        print(f"   Symbol: {df['symbol'].iloc[0]}")
        print(f"   Start: {df.index[0]}")
        print(f"   End: {df.index[-1]}")
        print(f"   Latest close: ${df['close'].iloc[-1]:,.2f}")

        # Calculate 24h change
        if len(df) >= 24:
            change_24h = ((df['close'].iloc[-1] / df['close'].iloc[-24] - 1) * 100)
            print(f"   24h change: {change_24h:.2f}%")

        # Display first and last rows
        print("\n4. First 3 rows:")
        print(df.head(3))

        print("\n5. Last 3 rows:")
        print(df.tail(3))

        # Basic statistics
        print("\n6. Statistics:")
        print(df[['open', 'high', 'low', 'close', 'volume']].describe())

        # Save to CSV
        output_file = f'{symbol}_{exchange}_{interval.value}.csv'
        df.to_csv(output_file)
        print(f"\n7. Data saved to {output_file}")

        # Example: Filter data
        print("\n8. Example analysis - High volume bars:")
        avg_volume = df['volume'].mean()
        high_volume_bars = df[df['volume'] > avg_volume * 1.5]
        print(f"   Found {len(high_volume_bars)} bars with volume > 150% of average")
        if len(high_volume_bars) > 0:
            print(f"   Max volume bar: {high_volume_bars['volume'].max():,.0f}")

    else:
        print("   ✗ Failed to download data")
        print("   Check symbol name and exchange")

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
