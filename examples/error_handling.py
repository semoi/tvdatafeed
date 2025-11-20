"""
Error handling example

This example demonstrates:
- Proper error handling when fetching data
- Handling authentication errors
- Dealing with invalid symbols
- Timeout handling
"""
import os
import logging
from tvDatafeed import TvDatafeed, Interval

# Setup logging to see detailed error messages
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def safe_fetch_data(tv, symbol, exchange, interval, n_bars=10):
    """
    Safely fetch data with error handling

    Parameters
    ----------
    tv : TvDatafeed
        TvDatafeed instance
    symbol : str
        Symbol to fetch
    exchange : str
        Exchange name
    interval : Interval
        Time interval
    n_bars : int
        Number of bars

    Returns
    -------
    pd.DataFrame or None
        DataFrame if successful, None if failed
    """
    try:
        logger.info(f"Fetching {symbol} from {exchange}...")

        df = tv.get_hist(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            n_bars=n_bars
        )

        if df is not None and not df.empty:
            logger.info(f"✓ Success: {len(df)} bars retrieved")
            logger.info(f"  Latest close: ${df['close'].iloc[-1]:.2f}")
            return df
        else:
            logger.warning(f"⚠ No data returned for {symbol}")
            return None

    except ValueError as e:
        logger.error(f"✗ Value Error: {e}")
        logger.info("  → Check that symbol and exchange are valid")
        return None

    except TimeoutError as e:
        logger.error(f"✗ Timeout Error: {e}")
        logger.info("  → Try increasing timeout or check your network")
        return None

    except ConnectionError as e:
        logger.error(f"✗ Connection Error: {e}")
        logger.info("  → Check your internet connection")
        return None

    except Exception as e:
        logger.error(f"✗ Unexpected Error: {type(e).__name__}: {e}")
        logger.info("  → This might be a bug, please report it")
        return None


def test_authentication():
    """Test different authentication scenarios"""
    print("\n" + "=" * 60)
    print("Testing Authentication Scenarios")
    print("=" * 60)

    # Scenario 1: No authentication
    print("\n1. No authentication (limited access):")
    try:
        tv = TvDatafeed()
        logger.info("✓ Connected without authentication")
    except Exception as e:
        logger.error(f"✗ Failed to connect: {e}")

    # Scenario 2: With credentials from environment
    print("\n2. With credentials from environment variables:")
    try:
        username = os.getenv('TV_USERNAME')
        password = os.getenv('TV_PASSWORD')

        if username and password:
            tv = TvDatafeed(username=username, password=password)
            logger.info("✓ Authenticated successfully")
        else:
            logger.warning("⚠ No credentials in environment variables")
            logger.info("  Set TV_USERNAME and TV_PASSWORD to test authentication")

    except Exception as e:
        logger.error(f"✗ Authentication failed: {e}")
        logger.info("  → Check your username and password")
        logger.info("  → If 2FA is enabled, you need to provide the code")


def test_data_fetching():
    """Test fetching data with various scenarios"""
    print("\n" + "=" * 60)
    print("Testing Data Fetching Scenarios")
    print("=" * 60)

    tv = TvDatafeed()

    # Scenario 1: Valid symbol
    print("\n1. Valid symbol (BTCUSDT on BINANCE):")
    safe_fetch_data(tv, 'BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=10)

    # Scenario 2: Invalid symbol name
    print("\n2. Invalid symbol:")
    safe_fetch_data(tv, 'INVALID_SYMBOL', 'BINANCE', Interval.in_1_hour, n_bars=10)

    # Scenario 3: Wrong exchange
    print("\n3. Symbol on wrong exchange:")
    safe_fetch_data(tv, 'BTCUSDT', 'NYSE', Interval.in_1_hour, n_bars=10)

    # Scenario 4: Too many bars requested
    print("\n4. Requesting too many bars (max is 5000):")
    safe_fetch_data(tv, 'BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=5000)


def test_symbol_search():
    """Test symbol search functionality"""
    print("\n" + "=" * 60)
    print("Testing Symbol Search")
    print("=" * 60)

    tv = TvDatafeed()

    # Search for Bitcoin
    print("\n1. Searching for 'BTC' on BINANCE:")
    try:
        results = tv.search_symbol('BTC', 'BINANCE')

        if results:
            logger.info(f"✓ Found {len(results)} results")
            for i, result in enumerate(results[:5], 1):  # Show first 5
                logger.info(f"  {i}. {result.get('symbol')} - {result.get('description', 'N/A')}")
        else:
            logger.warning("⚠ No results found")

    except Exception as e:
        logger.error(f"✗ Search failed: {e}")

    # Search on all exchanges
    print("\n2. Searching for 'AAPL' (any exchange):")
    try:
        results = tv.search_symbol('AAPL', '')

        if results:
            logger.info(f"✓ Found {len(results)} results")
            for i, result in enumerate(results[:5], 1):
                logger.info(f"  {i}. {result.get('symbol')} on {result.get('exchange', 'N/A')}")
        else:
            logger.warning("⚠ No results found")

    except Exception as e:
        logger.error(f"✗ Search failed: {e}")


def main():
    """Main function"""
    print("=" * 60)
    print("TvDatafeed - Error Handling Examples")
    print("=" * 60)

    # Run tests
    test_authentication()
    test_data_fetching()
    test_symbol_search()

    print("\n" + "=" * 60)
    print("Error handling examples completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
