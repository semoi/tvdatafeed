"""
Automated Data Fetching Example

This example shows how to run TvDatafeed in an automated/scheduled environment
(e.g., cron job, Windows Task Scheduler, or server script).

The token_manager handles:
- Checking if the current token is valid
- Automatically refreshing the token when it's about to expire
- Caching tokens securely

Setup:
    1. Install dependencies:
       pip install playwright playwright-stealth pyotp
       playwright install chromium

    2. Configure .env file:
       TV_USERNAME=your_username
       TV_PASSWORD=your_password
       TV_TOTP_SECRET=your_totp_secret  # Optional, for 2FA

    3. Run initial token extraction:
       python scripts/get_auth_token.py

    4. Schedule this script (cron, Task Scheduler, etc.)

Usage:
    python examples/automated_data_fetch.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def fetch_data():
    """Main data fetching function"""
    from tvDatafeed import TvDatafeed, Interval

    # Import token manager
    try:
        from scripts.token_manager import get_valid_token, get_token_info
    except ImportError:
        logger.error("Could not import token_manager. Make sure you're running from project root.")
        sys.exit(1)

    # Get valid token (auto-refreshes if needed)
    logger.info("Getting valid auth token...")
    token = get_valid_token(auto_refresh=True)

    if not token:
        logger.error("Could not obtain valid token. Check your credentials.")
        sys.exit(1)

    # Log token info
    info = get_token_info(token)
    logger.info(f"Using token for plan: {info.get('plan')}")
    logger.info(f"Token expires: {info.get('expires_at')}")
    logger.info(f"Time remaining: {info.get('time_remaining')}")

    # Create TvDatafeed instance
    tv = TvDatafeed(auth_token=token, verbose=False)

    # Define symbols to fetch
    symbols = [
        ('BTCUSDT', 'BINANCE'),
        ('ETHUSDT', 'BINANCE'),
        ('AAPL', 'NASDAQ'),
        ('EURUSD', 'FX'),
    ]

    results = {}

    for symbol, exchange in symbols:
        try:
            logger.info(f"Fetching {exchange}:{symbol}...")
            df = tv.get_hist(
                symbol=symbol,
                exchange=exchange,
                interval=Interval.in_1_hour,
                n_bars=100
            )

            if df is not None and not df.empty:
                results[f"{exchange}:{symbol}"] = {
                    'status': 'success',
                    'rows': len(df),
                    'last_close': df['close'].iloc[-1],
                    'last_time': str(df.index[-1])
                }
                logger.info(f"  Got {len(df)} bars, last close: {df['close'].iloc[-1]:.2f}")
            else:
                results[f"{exchange}:{symbol}"] = {
                    'status': 'no_data'
                }
                logger.warning(f"  No data returned")

        except Exception as e:
            results[f"{exchange}:{symbol}"] = {
                'status': 'error',
                'error': str(e)
            }
            logger.error(f"  Error: {e}")

    return results


def save_results(results: dict, output_dir: Path = None):
    """Save results to file"""
    import json

    if output_dir is None:
        output_dir = project_root / 'data'

    output_dir.mkdir(exist_ok=True)

    # Save with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'fetch_results_{timestamp}.json'

    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, indent=2)

    logger.info(f"Results saved to {output_file}")


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Starting automated data fetch")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    try:
        results = fetch_data()
        save_results(results)

        # Summary
        success = sum(1 for r in results.values() if r.get('status') == 'success')
        total = len(results)
        logger.info(f"Completed: {success}/{total} symbols fetched successfully")

        return 0 if success == total else 1

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
