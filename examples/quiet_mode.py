"""
Verbose Logging Control Example

This example demonstrates:
- Default verbose mode (all logs)
- Quiet mode for production (only warnings/errors)
- Environment variable configuration
- When to use each mode
"""
import os
import logging
from tvDatafeed import TvDatafeed, Interval


def setup_logging(level=logging.INFO):
    """Configure logging for this example"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def example_verbose_mode():
    """Example 1: Verbose mode (default) - Shows all logs"""
    print("=" * 80)
    print("EXAMPLE 1: Verbose Mode (Default)")
    print("=" * 80)
    print("\nVerbose mode shows:")
    print("  ✓ Info messages (connection, authentication, progress)")
    print("  ✓ Warnings (non-critical issues)")
    print("  ✓ Errors (critical failures)")
    print("\nUse this mode when developing, debugging, or learning the library.\n")

    # Setup logging to see everything
    setup_logging(logging.INFO)

    print("-" * 80)
    print("Creating TvDatafeed with verbose=True (default)...")
    print("-" * 80)

    # Create instance with verbose mode (default)
    tv = TvDatafeed(verbose=True)

    # Download data - you'll see detailed progress logs
    print("\nDownloading data with verbose logs...")
    df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=10)

    if df is not None and not df.empty:
        print(f"\n✓ Successfully downloaded {len(df)} bars")
        print(f"  Latest price: ${df['close'].iloc[-1]:,.2f}")

    print("\n" + "=" * 80)


def example_quiet_mode():
    """Example 2: Quiet mode - Only warnings and errors"""
    print("\n\n")
    print("=" * 80)
    print("EXAMPLE 2: Quiet Mode (Production)")
    print("=" * 80)
    print("\nQuiet mode shows:")
    print("  ✗ Info messages suppressed")
    print("  ✓ Warnings still shown")
    print("  ✓ Errors still shown")
    print("\nUse this mode in production, scheduled tasks, or when you want clean logs.\n")

    # Setup logging - even if we set to INFO, TvDatafeed will filter its own logs
    setup_logging(logging.INFO)

    print("-" * 80)
    print("Creating TvDatafeed with verbose=False (quiet mode)...")
    print("-" * 80)

    # Create instance with quiet mode
    tv = TvDatafeed(verbose=False)

    # Download data - you'll see NO info logs, only warnings/errors if they occur
    print("\nDownloading data with quiet logs (no info messages)...")
    df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=10)

    if df is not None and not df.empty:
        print(f"\n✓ Successfully downloaded {len(df)} bars")
        print(f"  Latest price: ${df['close'].iloc[-1]:,.2f}")
        print("\nNotice: No info logs were shown above!")

    print("\n" + "=" * 80)


def example_environment_variable():
    """Example 3: Control via environment variable"""
    print("\n\n")
    print("=" * 80)
    print("EXAMPLE 3: Environment Variable Configuration")
    print("=" * 80)
    print("\nYou can also control verbosity via TV_VERBOSE environment variable:")
    print("  export TV_VERBOSE=false    # Quiet mode")
    print("  export TV_VERBOSE=true     # Verbose mode")
    print("\nParameter takes priority over environment variable.\n")

    # Demonstrate environment variable
    print("-" * 80)
    print("Setting TV_VERBOSE=false in environment...")
    print("-" * 80)

    # Set environment variable
    os.environ['TV_VERBOSE'] = 'false'

    # Create instance without specifying verbose parameter
    # It will read from environment variable
    tv = TvDatafeed()

    print(f"\nTvDatafeed instance created with verbose={tv.verbose}")
    print("(Read from TV_VERBOSE environment variable)")

    # Download data - will be quiet because env var is 'false'
    print("\nDownloading data (using environment variable setting)...")
    df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=10)

    if df is not None and not df.empty:
        print(f"\n✓ Successfully downloaded {len(df)} bars")
        print(f"  Latest price: ${df['close'].iloc[-1]:,.2f}")

    # Clean up
    del os.environ['TV_VERBOSE']

    print("\n" + "=" * 80)


def example_parameter_override():
    """Example 4: Parameter overrides environment variable"""
    print("\n\n")
    print("=" * 80)
    print("EXAMPLE 4: Parameter Priority")
    print("=" * 80)
    print("\nWhen both are set, parameter takes priority over environment variable.\n")

    # Set environment variable to true
    os.environ['TV_VERBOSE'] = 'true'
    print("Environment variable: TV_VERBOSE=true")

    # But override with parameter
    print("Parameter: verbose=False")
    print("\nCreating TvDatafeed(verbose=False)...")

    tv = TvDatafeed(verbose=False)

    print(f"Result: tv.verbose = {tv.verbose}")
    print("Parameter wins! Quiet mode will be used.\n")

    # Clean up
    del os.environ['TV_VERBOSE']

    print("=" * 80)


def example_production_use_case():
    """Example 5: Production use case"""
    print("\n\n")
    print("=" * 80)
    print("EXAMPLE 5: Production Use Case")
    print("=" * 80)
    print("\nTypical production configuration with clean logs:\n")

    # Production-style logging configuration
    logging.basicConfig(
        level=logging.WARNING,  # Root logger only shows warnings and errors
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    print("-" * 80)
    print("Production configuration:")
    print("  - Root logger: logging.WARNING")
    print("  - TvDatafeed: verbose=False")
    print("  - Result: Clean logs, only critical messages")
    print("-" * 80)

    # Create quiet instance for production
    tv = TvDatafeed(verbose=False)

    print("\nDownloading data in production mode...")
    print("(You should see no info logs, only this message and results)\n")

    # Download multiple symbols
    symbols = [
        ('BTCUSDT', 'BINANCE'),
        ('ETHUSDT', 'BINANCE'),
    ]

    results = {}
    for symbol, exchange in symbols:
        df = tv.get_hist(symbol, exchange, Interval.in_1_hour, n_bars=10)
        if df is not None and not df.empty:
            results[symbol] = df['close'].iloc[-1]

    print("Results:")
    for symbol, price in results.items():
        print(f"  {symbol}: ${price:,.2f}")

    print("\n" + "=" * 80)


def print_summary():
    """Print summary of when to use each mode"""
    print("\n\n")
    print("=" * 80)
    print("SUMMARY: When to Use Each Mode")
    print("=" * 80)

    print("\n📢 VERBOSE MODE (verbose=True - Default)")
    print("   Use when:")
    print("   ✓ Developing and debugging your code")
    print("   ✓ Learning how TvDatafeed works")
    print("   ✓ Troubleshooting connection or authentication issues")
    print("   ✓ You want to see detailed progress information")
    print("   ✓ Running interactively in Jupyter notebooks")

    print("\n🔇 QUIET MODE (verbose=False)")
    print("   Use when:")
    print("   ✓ Running in production environments")
    print("   ✓ Scheduled/automated tasks (cron jobs, etc.)")
    print("   ✓ Clean log output is important")
    print("   ✓ You only care about errors and warnings")
    print("   ✓ Running as a service or daemon")

    print("\n💡 CONFIGURATION METHODS:")
    print("   1. Parameter:           TvDatafeed(verbose=False)")
    print("   2. Environment var:     export TV_VERBOSE=false")
    print("   3. Priority:            Parameter > Env var > Default (True)")

    print("\n⚠️  REMEMBER:")
    print("   • Errors and warnings are ALWAYS shown, regardless of mode")
    print("   • Quiet mode only suppresses info and debug messages")
    print("   • You can change the root logger level independently")

    print("\n" + "=" * 80)


def main():
    """Run all examples"""
    print("\n")
    print("*" * 80)
    print("*" + " " * 78 + "*")
    print("*" + " " * 20 + "TvDatafeed - Verbose Logging Control" + " " * 22 + "*")
    print("*" + " " * 78 + "*")
    print("*" * 80)

    # Run examples
    try:
        example_verbose_mode()
        input("\nPress Enter to continue to Example 2...")

        example_quiet_mode()
        input("\nPress Enter to continue to Example 3...")

        example_environment_variable()
        input("\nPress Enter to continue to Example 4...")

        example_parameter_override()
        input("\nPress Enter to continue to Example 5...")

        example_production_use_case()

        print_summary()

        print("\n✅ All examples completed successfully!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
