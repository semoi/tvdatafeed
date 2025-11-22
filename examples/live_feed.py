"""
Live data feed example for TvDatafeedLive

This example demonstrates:
- Creating a live data feed
- Setting up callbacks for new data
- Monitoring multiple symbols
- Proper cleanup
"""
import os
import time
from tvDatafeed import TvDatafeedLive, Interval


def on_btc_data(seis, data):
    """
    Callback for Bitcoin data

    This function is called whenever new data is available for BTC

    Parameters
    ----------
    seis : Seis
        The Seis instance (contains symbol, exchange, interval info)
    data : pd.DataFrame
        New data bar(s)
    """
    # Extract latest bar
    latest = data.iloc[-1]

    print(f"\n📊 New BTC data received!")
    print(f"   Time: {data.index[-1]}")
    print(f"   Open: ${latest['open']:,.2f}")
    print(f"   High: ${latest['high']:,.2f}")
    print(f"   Low: ${latest['low']:,.2f}")
    print(f"   Close: ${latest['close']:,.2f}")
    print(f"   Volume: {latest['volume']:,.0f}")


def on_eth_data(seis, data):
    """Callback for Ethereum data"""
    latest = data.iloc[-1]

    print(f"\n📊 New ETH data received!")
    print(f"   Time: {data.index[-1]}")
    print(f"   Close: ${latest['close']:,.2f}")


def multi_symbol_callback(seis, data):
    """
    Generic callback that works for multiple symbols

    This callback prints a simple message for any symbol
    """
    latest = data.iloc[-1]
    print(f"📈 {seis.symbol} @ ${latest['close']:,.2f}")


def main():
    """Main example function"""
    print("=" * 60)
    print("TvDatafeedLive - Live Data Feed Example")
    print("=" * 60)

    # Connect with authentication (required for live data)
    print("\n1. Connecting to TradingView...")

    # Option 1: Use environment variables (recommended)
    tvl = TvDatafeedLive(
        username=os.getenv('TV_USERNAME'),
        password=os.getenv('TV_PASSWORD')
    )

    # Option 2: Direct credentials (not recommended)
    # tvl = TvDatafeedLive(username='your_username', password='your_password')

    print("   ✓ Connected successfully")

    # Create SEIS (Symbol-Exchange-Interval Set) for Bitcoin
    print("\n2. Setting up live feed for BTCUSDT (1 minute bars)...")
    btc_seis = tvl.new_seis(
        symbol='BTCUSDT',
        exchange='BINANCE',
        interval=Interval.in_1_minute
    )
    print("   ✓ BTC seis created")

    # Create SEIS for Ethereum
    print("\n3. Setting up live feed for ETHUSDT (1 minute bars)...")
    eth_seis = tvl.new_seis(
        symbol='ETHUSDT',
        exchange='BINANCE',
        interval=Interval.in_1_minute
    )
    print("   ✓ ETH seis created")

    # Register callbacks
    print("\n4. Registering callbacks...")
    btc_consumer = tvl.new_consumer(btc_seis, on_btc_data)
    eth_consumer = tvl.new_consumer(eth_seis, on_eth_data)
    print("   ✓ Callbacks registered")

    # Example: Multiple consumers for same seis
    print("\n5. Adding second callback for BTC (multi-consumer example)...")
    btc_consumer2 = tvl.new_consumer(btc_seis, multi_symbol_callback)
    print("   ✓ Second BTC callback registered")

    # Let it run for a specified duration
    duration = 300  # 5 minutes
    print(f"\n6. Monitoring live data for {duration} seconds...")
    print("   (Press Ctrl+C to stop early)")
    print("\n" + "-" * 60)

    try:
        time.sleep(duration)
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")

    # Cleanup
    print("\n" + "-" * 60)
    print("\n7. Cleaning up...")

    # Remove consumers
    print("   Removing consumers...")
    tvl.del_consumer(btc_consumer)
    tvl.del_consumer(btc_consumer2)
    tvl.del_consumer(eth_consumer)

    # Remove seis
    print("   Removing seis...")
    tvl.del_seis(btc_seis)
    tvl.del_seis(eth_seis)

    print("   ✓ Cleanup complete")

    print("\n" + "=" * 60)
    print("Live feed example completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
