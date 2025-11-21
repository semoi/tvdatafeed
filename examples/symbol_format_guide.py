#!/usr/bin/env python3
"""
Symbol Format Guide - TvDatafeed

This example demonstrates:
1. Correct symbol format (EXCHANGE:SYMBOL)
2. How to use search_symbol() to find correct symbols
3. Common mistakes and how to fix them
4. Timeout configuration for slow connections
5. Best practices for reliable data retrieval

IMPORTANT: This addresses Issue #63 - tv.get_hist() stopped working
The main issue is usually incorrect symbol format or timeout errors.
"""

import logging
import os
from tvDatafeed import TvDatafeed, Interval
from tvDatafeed.exceptions import (
    DataNotFoundError,
    WebSocketTimeoutError,
    DataValidationError
)

# Enable debug logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_1_correct_format():
    """Example 1: Using correct EXCHANGE:SYMBOL format"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Correct Symbol Format (EXCHANGE:SYMBOL)")
    print("="*80)

    tv = TvDatafeed()

    # ✅ CORRECT: Using full EXCHANGE:SYMBOL format
    symbols = [
        ('BINANCE:BTCUSDT', 'BINANCE', 'Bitcoin on Binance'),
        ('NASDAQ:AAPL', 'NASDAQ', 'Apple Inc.'),
        ('NSE:NIFTY', 'NSE', 'Nifty 50 Index'),
    ]

    for symbol, exchange, description in symbols:
        try:
            print(f"\n✅ Fetching {description}: {symbol}")
            df = tv.get_hist(
                symbol=symbol,
                exchange=exchange,
                interval=Interval.in_daily,
                n_bars=5
            )
            print(f"   Success! Retrieved {len(df)} bars")
            print(f"   Latest close: {df.iloc[-1]['close']:.2f}")

        except DataNotFoundError as e:
            print(f"   ❌ No data found: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")


def example_2_search_symbol():
    """Example 2: Using search_symbol() to find correct format"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Using search_symbol() to Find Correct Format")
    print("="*80)

    tv = TvDatafeed()

    search_queries = [
        ('BTC', 'BINANCE', 'Bitcoin on Binance'),
        ('AAPL', 'NASDAQ', 'Apple stock'),
        ('ETH', 'COINBASE', 'Ethereum on Coinbase'),
    ]

    for query, exchange, description in search_queries:
        print(f"\n🔍 Searching for '{query}' on {exchange} ({description})")

        try:
            results = tv.search_symbol(query, exchange)

            if not results:
                print(f"   ⚠️  No results found. Try searching on tradingview.com")
                continue

            print(f"   Found {len(results)} results:")

            # Show first 3 results
            for i, result in enumerate(results[:3], 1):
                full_symbol = f"{result.get('exchange', 'N/A')}:{result.get('symbol', 'N/A')}"
                desc = result.get('description', 'N/A')
                print(f"   {i}. {full_symbol:30s} - {desc}")

            # Try to fetch data with the first result
            if results:
                first = results[0]
                symbol = f"{first['exchange']}:{first['symbol']}"
                print(f"\n   📊 Fetching data for {symbol}...")

                df = tv.get_hist(
                    symbol=symbol,
                    exchange=first['exchange'],
                    interval=Interval.in_1_hour,
                    n_bars=5
                )
                print(f"   ✅ Success! Retrieved {len(df)} bars")

        except DataValidationError as e:
            print(f"   ❌ Validation error: {e}")
        except DataNotFoundError as e:
            print(f"   ❌ No data found: {e}")
        except Exception as e:
            print(f"   ❌ Error: {type(e).__name__}: {e}")


def example_3_format_search_results():
    """Example 3: Using format_search_results() for nice display"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Formatted Search Results")
    print("="*80)

    tv = TvDatafeed()

    print("\n🔍 Searching for 'BTC' on BINANCE:")
    results = tv.search_symbol('BTC', 'BINANCE')

    if results:
        # Use the helper method to format results
        formatted = tv.format_search_results(results, max_results=5)
        print(formatted)
    else:
        print("   ⚠️  No results found")


def example_4_common_mistakes():
    """Example 4: Common mistakes and how to fix them"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Common Mistakes and Fixes")
    print("="*80)

    tv = TvDatafeed()

    # Mistake 1: Symbol without exchange prefix
    print("\n❌ MISTAKE 1: Using symbol without EXCHANGE prefix")
    print("   Code: tv.get_hist('BTCUSDT', 'BINANCE', ...)")
    print("   This MIGHT work but is less reliable")

    try:
        df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=5)
        print(f"   ⚠️  Worked this time, but not guaranteed. Retrieved {len(df)} bars")
    except DataNotFoundError:
        print("   ❌ Failed! This is why you should use EXCHANGE:SYMBOL format")

    print("\n✅ FIX 1: Use full EXCHANGE:SYMBOL format")
    print("   Code: tv.get_hist('BINANCE:BTCUSDT', 'BINANCE', ...)")
    try:
        df = tv.get_hist('BINANCE:BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=5)
        print(f"   ✅ Success! Retrieved {len(df)} bars")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Mistake 2: Wrong exchange
    print("\n❌ MISTAKE 2: Using wrong exchange")
    print("   Code: tv.get_hist('BTCUSDT', 'NYSE', ...)  # Bitcoin is not on NYSE!")

    try:
        df = tv.get_hist('BTCUSDT', 'NYSE', Interval.in_daily, n_bars=5)
        print(f"   Unexpected success?")
    except DataNotFoundError as e:
        print(f"   ❌ Expected failure: Symbol not found on this exchange")

    print("\n✅ FIX 2: Use correct exchange")
    print("   Code: tv.get_hist('BINANCE:BTCUSDT', 'BINANCE', ...)")

    # Mistake 3: Typo in symbol name
    print("\n❌ MISTAKE 3: Typo in symbol name")
    print("   Code: tv.get_hist('BTCUSD', 'BINANCE', ...)  # Should be BTCUSDT")

    try:
        df = tv.get_hist('BTCUSD', 'BINANCE', Interval.in_daily, n_bars=5)
        print(f"   Retrieved {len(df)} bars (might be a different pair)")
    except DataNotFoundError:
        print(f"   ❌ No data found")

    print("\n✅ FIX 3: Use search_symbol() to find exact name")
    print("   Code: results = tv.search_symbol('BTC', 'BINANCE')")


def example_5_timeout_configuration():
    """Example 5: Configuring timeout for slow connections"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Timeout Configuration")
    print("="*80)

    # Method 1: Default timeout (5 seconds)
    print("\n📊 Method 1: Default timeout (5 seconds)")
    print("   tv = TvDatafeed()")
    tv_default = TvDatafeed()
    print(f"   WebSocket timeout: {tv_default.ws_timeout}s")

    # Method 2: Custom timeout via parameter
    print("\n📊 Method 2: Custom timeout via parameter")
    print("   tv = TvDatafeed(ws_timeout=30.0)")
    tv_custom = TvDatafeed(ws_timeout=30.0)
    print(f"   WebSocket timeout: {tv_custom.ws_timeout}s")

    # Method 3: Environment variable
    print("\n📊 Method 3: Environment variable")
    print("   export TV_WS_TIMEOUT=60.0")
    print("   tv = TvDatafeed()")
    os.environ['TV_WS_TIMEOUT'] = '60.0'
    tv_env = TvDatafeed()
    print(f"   WebSocket timeout: {tv_env.ws_timeout}s")

    # Clean up
    os.environ.pop('TV_WS_TIMEOUT', None)

    # Try with custom timeout
    print("\n📊 Testing with custom timeout (30s)...")
    tv_test = TvDatafeed(ws_timeout=30.0)

    try:
        df = tv_test.get_hist(
            'BINANCE:BTCUSDT',
            'BINANCE',
            Interval.in_1_hour,
            n_bars=100
        )
        print(f"   ✅ Success! Retrieved {len(df)} bars with 30s timeout")
    except WebSocketTimeoutError as e:
        print(f"   ⏱️  Timeout: {e}")
        print("   💡 Try increasing timeout further or check your connection")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def example_6_best_practices():
    """Example 6: Best practices for reliable data retrieval"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Best Practices")
    print("="*80)

    print("\n✅ Best Practice 1: Always use EXCHANGE:SYMBOL format")
    print("   symbol = 'BINANCE:BTCUSDT'  # Not just 'BTCUSDT'")

    print("\n✅ Best Practice 2: Use search_symbol() when unsure")
    print("   results = tv.search_symbol('BTC', 'BINANCE')")
    print("   symbol = f\"{results[0]['exchange']}:{results[0]['symbol']}\"")

    print("\n✅ Best Practice 3: Test with small n_bars first")
    print("   df = tv.get_hist(symbol, exchange, interval, n_bars=10)  # Start small")
    print("   # Then increase if successful")

    print("\n✅ Best Practice 4: Increase timeout for large requests")
    print("   tv = TvDatafeed(ws_timeout=30.0)  # For n_bars > 1000")

    print("\n✅ Best Practice 5: Handle errors gracefully")
    print("   try:")
    print("       df = tv.get_hist(...)")
    print("   except DataNotFoundError:")
    print("       # Check symbol format")
    print("   except WebSocketTimeoutError:")
    print("       # Increase timeout")

    print("\n✅ Best Practice 6: Enable debug logging for troubleshooting")
    print("   import logging")
    print("   logging.basicConfig(level=logging.DEBUG)")
    print("   tv.ws_debug = True")


def example_7_real_world_workflow():
    """Example 7: Complete real-world workflow"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Real-World Workflow")
    print("="*80)

    print("\n📋 Scenario: Fetch Bitcoin data from Binance")
    print("="*60)

    # Step 1: Search for symbol
    print("\n1️⃣  Search for symbol to get exact format:")
    tv = TvDatafeed(ws_timeout=30.0)  # Use longer timeout

    results = tv.search_symbol('BTC', 'BINANCE')
    if not results:
        print("   ❌ No results found. Check exchange name or network connection.")
        return

    print(f"   ✅ Found {len(results)} results")
    first = results[0]
    symbol = f"{first['exchange']}:{first['symbol']}"
    exchange = first['exchange']
    print(f"   📍 Using: {symbol}")

    # Step 2: Test with small request
    print("\n2️⃣  Test with small request (10 bars):")
    try:
        df_test = tv.get_hist(symbol, exchange, Interval.in_1_hour, n_bars=10)
        print(f"   ✅ Test successful! Retrieved {len(df_test)} bars")
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        print("   💡 Try increasing timeout or check symbol format")
        return

    # Step 3: Fetch full dataset
    print("\n3️⃣  Fetch full dataset (500 bars):")
    try:
        df = tv.get_hist(symbol, exchange, Interval.in_1_hour, n_bars=500)
        print(f"   ✅ Success! Retrieved {len(df)} bars")

        # Step 4: Display summary
        print("\n4️⃣  Data summary:")
        print(f"   Date range: {df.index[0]} to {df.index[-1]}")
        print(f"   Latest close: ${df.iloc[-1]['close']:.2f}")
        print(f"   High: ${df['close'].max():.2f}")
        print(f"   Low: ${df['close'].min():.2f}")
        print(f"   Average volume: {df['volume'].mean():,.0f}")

        # Step 5: Ready for analysis
        print("\n5️⃣  Data ready for analysis!")
        print("   # Now you can use this data with pandas, TA-Lib, etc.")
        print("   # df['SMA_20'] = talib.SMA(df['close'], timeperiod=20)")

    except WebSocketTimeoutError:
        print("   ⏱️  Timeout occurred. Try:")
        print("      - Increase timeout: tv = TvDatafeed(ws_timeout=60.0)")
        print("      - Reduce n_bars")
        print("      - Check your internet connection")
    except DataNotFoundError as e:
        print(f"   ❌ No data found: {e}")
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("TvDatafeed - Symbol Format Guide")
    print("Solving Issue #63: tv.get_hist() stopped working")
    print("="*80)

    examples = [
        ("Correct Symbol Format", example_1_correct_format),
        ("Using search_symbol()", example_2_search_symbol),
        ("Formatted Search Results", example_3_format_search_results),
        ("Common Mistakes", example_4_common_mistakes),
        ("Timeout Configuration", example_5_timeout_configuration),
        ("Best Practices", example_6_best_practices),
        ("Real-World Workflow", example_7_real_world_workflow),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nRunning all examples...")
    print("(To run individually, modify the main() function)")

    for name, example_func in examples:
        try:
            example_func()
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Example '{name}' failed: {e}")
            logger.exception(f"Error in {name}")

    print("\n" + "="*80)
    print("Examples completed!")
    print("="*80)
    print("\n💡 Key Takeaways:")
    print("   1. Always use EXCHANGE:SYMBOL format (e.g., 'BINANCE:BTCUSDT')")
    print("   2. Use search_symbol() to find correct symbol names")
    print("   3. Increase timeout for slow connections: TvDatafeed(ws_timeout=30.0)")
    print("   4. Test with small n_bars first, then increase")
    print("   5. Enable debug logging when troubleshooting")
    print("\n📚 See README.md for more information")
    print("🐛 Report issues at: https://github.com/rongardF/tvdatafeed/issues")


if __name__ == "__main__":
    main()
