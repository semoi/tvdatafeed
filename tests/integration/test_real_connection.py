"""
Real Integration Tests for TvDatafeed

These tests make REAL connections to TradingView WebSockets.
Run with: python -m pytest tests/integration/test_real_connection.py -v -s
Or directly: python tests/integration/test_real_connection.py

Requires .env file with valid credentials.
"""
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

import pandas as pd
from tvDatafeed import TvDatafeed, Interval


class RealIntegrationTests:
    """Real integration tests with TradingView"""

    def __init__(self):
        self.username = os.getenv('TV_USERNAME')
        self.password = os.getenv('TV_PASSWORD')
        self.totp_secret = os.getenv('TV_TOTP_SECRET')
        self.results = []
        self.tv = None

    def log_result(self, test_name: str, success: bool, message: str, duration: float = 0):
        """Log test result"""
        status = "PASS" if success else "FAIL"
        self.results.append({
            'test': test_name,
            'status': status,
            'message': message,
            'duration': round(duration, 2)
        })
        print(f"[{status}] {test_name}: {message} ({duration:.2f}s)")

    def test_1_authentication_with_2fa(self) -> bool:
        """Test 1: Authentication with 2FA/TOTP"""
        test_name = "Authentication with 2FA"
        start = time.time()

        try:
            print(f"\n{'='*60}")
            print(f"TEST: {test_name}")
            print(f"{'='*60}")
            print(f"Username: {self.username}")
            print(f"TOTP Secret: {'***' + self.totp_secret[-4:] if self.totp_secret else 'None'}")

            self.tv = TvDatafeed(
                username=self.username,
                password=self.password,
                totp_secret=self.totp_secret,
                verbose=True
            )

            duration = time.time() - start

            if self.tv.token:
                self.log_result(test_name, True, f"Token obtained: {self.tv.token[:20]}...", duration)
                return True
            else:
                self.log_result(test_name, False, "No token received", duration)
                return False

        except Exception as e:
            duration = time.time() - start
            self.log_result(test_name, False, f"Exception: {type(e).__name__}: {str(e)}", duration)
            return False

    def test_2_get_historical_data_crypto(self) -> bool:
        """Test 2: Get historical data for crypto (BTCUSDT)"""
        test_name = "Get Historical Data (BTCUSDT)"
        start = time.time()

        try:
            print(f"\n{'='*60}")
            print(f"TEST: {test_name}")
            print(f"{'='*60}")

            if not self.tv:
                self.log_result(test_name, False, "TvDatafeed not initialized", 0)
                return False

            df = self.tv.get_hist(
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=50
            )

            duration = time.time() - start

            if df is not None and not df.empty:
                print(f"\nDataFrame shape: {df.shape}")
                print(f"Columns: {list(df.columns)}")
                print(f"Date range: {df.index.min()} to {df.index.max()}")
                print(f"\nFirst 3 rows:")
                print(df.head(3))
                print(f"\nLast 3 rows:")
                print(df.tail(3))

                # Validate OHLCV data
                has_required_cols = all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume'])
                valid_ohlc = (df['high'] >= df['low']).all()

                if has_required_cols and valid_ohlc:
                    self.log_result(test_name, True, f"Got {len(df)} bars with valid OHLCV data", duration)
                    return True
                else:
                    self.log_result(test_name, False, "Invalid OHLCV data structure", duration)
                    return False
            else:
                self.log_result(test_name, False, "No data returned", duration)
                return False

        except Exception as e:
            duration = time.time() - start
            self.log_result(test_name, False, f"Exception: {type(e).__name__}: {str(e)}", duration)
            return False

    def test_3_get_historical_data_stock(self) -> bool:
        """Test 3: Get historical data for stock (AAPL)"""
        test_name = "Get Historical Data (AAPL)"
        start = time.time()

        try:
            print(f"\n{'='*60}")
            print(f"TEST: {test_name}")
            print(f"{'='*60}")

            if not self.tv:
                self.log_result(test_name, False, "TvDatafeed not initialized", 0)
                return False

            df = self.tv.get_hist(
                symbol='AAPL',
                exchange='NASDAQ',
                interval=Interval.in_daily,
                n_bars=30
            )

            duration = time.time() - start

            if df is not None and not df.empty:
                print(f"\nDataFrame shape: {df.shape}")
                print(f"Date range: {df.index.min()} to {df.index.max()}")
                print(f"\nLast 5 rows:")
                print(df.tail(5))

                self.log_result(test_name, True, f"Got {len(df)} bars for AAPL", duration)
                return True
            else:
                self.log_result(test_name, False, "No data returned", duration)
                return False

        except Exception as e:
            duration = time.time() - start
            self.log_result(test_name, False, f"Exception: {type(e).__name__}: {str(e)}", duration)
            return False

    def test_4_get_historical_data_forex(self) -> bool:
        """Test 4: Get historical data for forex (EURUSD)"""
        test_name = "Get Historical Data (EURUSD)"
        start = time.time()

        try:
            print(f"\n{'='*60}")
            print(f"TEST: {test_name}")
            print(f"{'='*60}")

            if not self.tv:
                self.log_result(test_name, False, "TvDatafeed not initialized", 0)
                return False

            df = self.tv.get_hist(
                symbol='EURUSD',
                exchange='FX',
                interval=Interval.in_4_hour,
                n_bars=50
            )

            duration = time.time() - start

            if df is not None and not df.empty:
                print(f"\nDataFrame shape: {df.shape}")
                print(f"Date range: {df.index.min()} to {df.index.max()}")
                print(f"\nLast 5 rows:")
                print(df.tail(5))

                self.log_result(test_name, True, f"Got {len(df)} bars for EURUSD", duration)
                return True
            else:
                self.log_result(test_name, False, "No data returned", duration)
                return False

        except Exception as e:
            duration = time.time() - start
            self.log_result(test_name, False, f"Exception: {type(e).__name__}: {str(e)}", duration)
            return False

    def test_5_multiple_intervals(self) -> bool:
        """Test 5: Test multiple timeframes"""
        test_name = "Multiple Intervals Test"
        start = time.time()

        try:
            print(f"\n{'='*60}")
            print(f"TEST: {test_name}")
            print(f"{'='*60}")

            if not self.tv:
                self.log_result(test_name, False, "TvDatafeed not initialized", 0)
                return False

            intervals_to_test = [
                (Interval.in_1_minute, "1m"),
                (Interval.in_5_minute, "5m"),
                (Interval.in_15_minute, "15m"),
                (Interval.in_1_hour, "1H"),
                (Interval.in_daily, "1D"),
            ]

            results = []
            for interval, name in intervals_to_test:
                try:
                    df = self.tv.get_hist(
                        symbol='BTCUSDT',
                        exchange='BINANCE',
                        interval=interval,
                        n_bars=10
                    )
                    if df is not None and not df.empty:
                        results.append((name, True, len(df)))
                        print(f"  [{name}] OK - {len(df)} bars")
                    else:
                        results.append((name, False, 0))
                        print(f"  [{name}] FAIL - No data")
                except Exception as e:
                    results.append((name, False, 0))
                    print(f"  [{name}] FAIL - {str(e)}")
                time.sleep(0.5)  # Small delay between requests

            duration = time.time() - start

            success_count = sum(1 for _, success, _ in results if success)
            total_count = len(results)

            if success_count == total_count:
                self.log_result(test_name, True, f"All {total_count} intervals OK", duration)
                return True
            elif success_count > 0:
                self.log_result(test_name, True, f"{success_count}/{total_count} intervals OK", duration)
                return True
            else:
                self.log_result(test_name, False, "All intervals failed", duration)
                return False

        except Exception as e:
            duration = time.time() - start
            self.log_result(test_name, False, f"Exception: {type(e).__name__}: {str(e)}", duration)
            return False

    def test_6_search_symbol(self) -> bool:
        """Test 6: Search for symbols"""
        test_name = "Symbol Search"
        start = time.time()

        try:
            print(f"\n{'='*60}")
            print(f"TEST: {test_name}")
            print(f"{'='*60}")

            if not self.tv:
                self.log_result(test_name, False, "TvDatafeed not initialized", 0)
                return False

            results = self.tv.search_symbol('BTC', 'BINANCE')

            duration = time.time() - start

            if results and len(results) > 0:
                print(f"\nFound {len(results)} results:")
                for i, r in enumerate(results[:5]):
                    print(f"  {i+1}. {r}")

                self.log_result(test_name, True, f"Found {len(results)} symbols", duration)
                return True
            else:
                self.log_result(test_name, False, "No results found", duration)
                return False

        except Exception as e:
            duration = time.time() - start
            self.log_result(test_name, False, f"Exception: {type(e).__name__}: {str(e)}", duration)
            return False

    def test_7_large_data_request(self) -> bool:
        """Test 7: Request large amount of data (1000 bars)"""
        test_name = "Large Data Request (1000 bars)"
        start = time.time()

        try:
            print(f"\n{'='*60}")
            print(f"TEST: {test_name}")
            print(f"{'='*60}")

            if not self.tv:
                self.log_result(test_name, False, "TvDatafeed not initialized", 0)
                return False

            df = self.tv.get_hist(
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                n_bars=20000
            )

            duration = time.time() - start

            if df is not None and not df.empty:
                print(f"\nDataFrame shape: {df.shape}")
                print(f"Date range: {df.index.min()} to {df.index.max()}")
                print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")

                if len(df) >= 19000:  # Allow some tolerance
                    self.log_result(test_name, True, f"Got {len(df)} bars", duration)
                    return True
                else:
                    self.log_result(test_name, False, f"Expected ~19000 bars, got {len(df)}", duration)
                    return False
            else:
                self.log_result(test_name, False, "No data returned", duration)
                return False

        except Exception as e:
            duration = time.time() - start
            self.log_result(test_name, False, f"Exception: {type(e).__name__}: {str(e)}", duration)
            return False

    def test_8_unauthenticated_access(self) -> bool:
        """Test 8: Unauthenticated access (limited data)"""
        test_name = "Unauthenticated Access"
        start = time.time()

        try:
            print(f"\n{'='*60}")
            print(f"TEST: {test_name}")
            print(f"{'='*60}")

            # Create new instance without credentials
            tv_unauth = TvDatafeed()

            df = tv_unauth.get_hist(
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=Interval.in_daily,
                n_bars=20
            )

            duration = time.time() - start

            if df is not None and not df.empty:
                print(f"\nDataFrame shape: {df.shape}")
                self.log_result(test_name, True, f"Got {len(df)} bars without auth", duration)
                return True
            else:
                self.log_result(test_name, False, "No data returned", duration)
                return False

        except Exception as e:
            duration = time.time() - start
            self.log_result(test_name, False, f"Exception: {type(e).__name__}: {str(e)}", duration)
            return False

    def generate_report(self):
        """Generate test report"""
        print(f"\n{'='*60}")
        print("TEST REPORT - TvDatafeed Real Integration Tests")
        print(f"{'='*60}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        total = len(self.results)
        total_duration = sum(r['duration'] for r in self.results)

        print(f"{'Test Name':<45} {'Status':<8} {'Duration':<10} Message")
        print("-" * 100)

        for r in self.results:
            status_icon = "OK" if r['status'] == 'PASS' else "FAIL"
            print(f"{r['test']:<45} {status_icon:<8} {r['duration']:<10.2f}s {r['message'][:40]}")

        print("-" * 100)
        print(f"\nSUMMARY:")
        print(f"  Total tests: {total}")
        print(f"  Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"  Failed: {failed} ({failed/total*100:.1f}%)")
        print(f"  Total duration: {total_duration:.2f}s")
        print(f"\n{'='*60}")

        return passed, failed, total

    def test_9_date_range_query(self) -> bool:
        """Test 9: Date range query feature"""
        test_name = "Date Range Query"
        start = time.time()

        try:
            print(f"\n{'='*60}")
            print(f"TEST: {test_name}")
            print(f"{'='*60}")

            if not self.tv:
                self.log_result(test_name, False, "TvDatafeed not initialized", 0)
                return False

            # Query last 7 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            df = self.tv.get_hist(
                symbol='BTCUSDT',
                exchange='BINANCE',
                interval=Interval.in_1_hour,
                start_date=start_date,
                end_date=end_date
            )

            duration = time.time() - start

            if df is not None and not df.empty:
                print(f"\nDataFrame shape: {df.shape}")
                print(f"Requested: {start_date} to {end_date}")
                print(f"Got: {df.index.min()} to {df.index.max()}")

                self.log_result(test_name, True, f"Got {len(df)} bars for date range", duration)
                return True
            else:
                self.log_result(test_name, False, "No data returned", duration)
                return False

        except Exception as e:
            duration = time.time() - start
            self.log_result(test_name, False, f"Exception: {type(e).__name__}: {str(e)}", duration)
            return False

    def run_all_tests(self, skip_auth: bool = False):
        """Run all integration tests"""
        print("\n" + "="*60)
        print("STARTING REAL INTEGRATION TESTS")
        print("="*60)
        print(f"Using credentials from .env file")
        print(f"Username: {self.username}")
        print(f"TOTP configured: {'Yes' if self.totp_secret else 'No'}")
        print(f"Skip authentication: {skip_auth}")
        print("="*60)

        if skip_auth:
            # Use unauthenticated access
            print("\nUsing UNAUTHENTICATED access for testing...")
            self.tv = TvDatafeed()
            self.log_result("Authentication with 2FA", False, "SKIPPED - Using unauthenticated mode", 0)

            tests = [
                self.test_2_get_historical_data_crypto,
                self.test_3_get_historical_data_stock,
                self.test_4_get_historical_data_forex,
                self.test_5_multiple_intervals,
                self.test_6_search_symbol,
                self.test_7_large_data_request,
                self.test_9_date_range_query,
            ]
        else:
            # Run tests in sequence with authentication
            tests = [
                self.test_1_authentication_with_2fa,
                self.test_2_get_historical_data_crypto,
                self.test_3_get_historical_data_stock,
                self.test_4_get_historical_data_forex,
                self.test_5_multiple_intervals,
                self.test_6_search_symbol,
                self.test_7_large_data_request,
                self.test_8_unauthenticated_access,
                self.test_9_date_range_query,
            ]

        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"Unexpected error in {test_func.__name__}: {e}")
            time.sleep(1)  # Delay between tests to avoid rate limiting

        return self.generate_report()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run real integration tests for TvDatafeed')
    parser.add_argument('--skip-auth', action='store_true',
                        help='Skip authentication and use unauthenticated access')
    args = parser.parse_args()

    tests = RealIntegrationTests()
    passed, failed, total = tests.run_all_tests(skip_auth=args.skip_auth)

    # Exit with error code if any tests failed
    sys.exit(0 if failed == 0 else 1)
