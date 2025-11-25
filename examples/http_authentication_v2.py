"""
HTTP Authentication Example (v2.0) - RECOMMENDED METHOD
========================================================

This example demonstrates the NEW HTTP authentication method introduced in v2.0
that automatically bypasses TradingView's reCAPTCHA without any manual intervention.

✅ No more CAPTCHA issues!
✅ No manual token extraction!
✅ Automatic 2FA support!
✅ Works in headless environments!

This is now the RECOMMENDED method for all authentication scenarios.
"""

import os
import logging
from pathlib import Path
from tvDatafeed import TvDatafeed, Interval
from tvDatafeed.exceptions import AuthenticationError, TwoFactorRequiredError

# Enable logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def load_env():
    """Load environment variables from .env file (optional)"""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip().strip('"').strip("'")
                    os.environ.setdefault(key, value)
        print(f"✓ Loaded environment from {env_file}\n")


def example_1_basic_auth():
    """
    Example 1: Basic HTTP authentication (no 2FA)

    This is the simplest case - just username and password.
    The HTTP method automatically bypasses reCAPTCHA.
    """
    print("=" * 70)
    print("EXAMPLE 1: Basic HTTP Authentication (No 2FA)")
    print("=" * 70)
    print()

    username = os.getenv('TV_USERNAME')
    password = os.getenv('TV_PASSWORD')

    if not username or not password:
        print("⚠ Missing credentials!")
        print("\nSet environment variables:")
        print("  export TV_USERNAME='your_username'")
        print("  export TV_PASSWORD='your_password'")
        return

    try:
        print("Authenticating with HTTP method (bypasses reCAPTCHA)...")

        tv = TvDatafeed(
            username=username,
            password=password
        )

        print("✓ Authentication successful!")
        print()

        # Test by fetching data
        print("Fetching BTCUSDT data from Binance...")
        df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=10)

        print(f"✓ Retrieved {len(df)} bars of data")
        print(f"\nLatest close price: ${df['close'].iloc[-1]:,.2f}")
        print()

    except AuthenticationError as e:
        print(f"✗ Authentication failed: {e}")
        print("\nCheck your credentials and try again.")

    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")


def example_2_with_2fa():
    """
    Example 2: HTTP authentication with automatic 2FA

    When you have 2FA enabled, just provide your TOTP secret.
    The library will automatically generate and submit the 2FA code.
    """
    print("=" * 70)
    print("EXAMPLE 2: HTTP Authentication with Automatic 2FA")
    print("=" * 70)
    print()

    username = os.getenv('TV_USERNAME')
    password = os.getenv('TV_PASSWORD')
    totp_secret = os.getenv('TV_TOTP_SECRET')

    if not all([username, password, totp_secret]):
        print("⚠ Missing credentials or TOTP secret!")
        print("\nSet environment variables:")
        print("  export TV_USERNAME='your_username'")
        print("  export TV_PASSWORD='your_password'")
        print("  export TV_TOTP_SECRET='YOUR_TOTP_SECRET'")
        print()
        print_totp_setup_guide()
        return

    try:
        print("Authenticating with HTTP method + automatic 2FA...")

        tv = TvDatafeed(
            username=username,
            password=password,
            totp_secret=totp_secret  # Automatic 2FA!
        )

        print("✓ Authentication successful (2FA handled automatically)!")
        print()

        # Test by fetching data
        print("Fetching BTCUSDT data from Binance...")
        df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=10)

        print(f"✓ Retrieved {len(df)} bars of data")
        print(f"\nLatest close price: ${df['close'].iloc[-1]:,.2f}")
        print()

    except TwoFactorRequiredError as e:
        print(f"✗ 2FA error: {e}")
        print("\nMake sure your TOTP secret is correct.")
        print_totp_setup_guide()

    except AuthenticationError as e:
        print(f"✗ Authentication failed: {e}")

    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")


def example_3_production_ready():
    """
    Example 3: Production-ready configuration

    This example shows best practices for production deployments:
    - Load credentials from environment
    - Proper error handling
    - Logging configuration
    - Connection testing
    """
    print("=" * 70)
    print("EXAMPLE 3: Production-Ready Configuration")
    print("=" * 70)
    print()

    # Load credentials from environment
    username = os.getenv('TV_USERNAME')
    password = os.getenv('TV_PASSWORD')
    totp_secret = os.getenv('TV_TOTP_SECRET')  # Optional (only if 2FA enabled)

    if not username or not password:
        print("✗ Missing required credentials")
        print("\nConfigure environment variables or .env file")
        return

    try:
        print("Initializing TvDatafeed with HTTP authentication...")

        # Initialize with all available credentials
        tv = TvDatafeed(
            username=username,
            password=password,
            totp_secret=totp_secret,  # Will be used only if 2FA is enabled
            verbose=False  # Set to True for debugging
        )

        print("✓ Initialized successfully")
        print()

        # Test connection with a simple request
        print("Testing connection...")
        test_symbols = [
            ('BTCUSDT', 'BINANCE'),
            ('AAPL', 'NASDAQ'),
            ('EURUSD', 'FX_IDC')
        ]

        for symbol, exchange in test_symbols:
            try:
                df = tv.get_hist(symbol, exchange, Interval.in_daily, n_bars=5)
                print(f"  ✓ {symbol:10s} ({exchange:10s}): {len(df)} bars - Latest: {df['close'].iloc[-1]:.2f}")
            except Exception as e:
                print(f"  ✗ {symbol:10s} ({exchange:10s}): {e}")

        print()
        print("✓ Connection test completed")
        print()

    except AuthenticationError as e:
        print(f"✗ Authentication failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify your credentials are correct")
        print("  2. If 2FA is enabled, ensure TOTP secret is configured")
        print("  3. Check your TradingView account status")

    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


def example_4_comparing_auth_methods():
    """
    Example 4: Comparing authentication methods

    Shows the difference between:
    - HTTP auth (v2.0 - RECOMMENDED)
    - JWT token auth (legacy - still supported)
    - No auth (limited access)
    """
    print("=" * 70)
    print("EXAMPLE 4: Comparing Authentication Methods")
    print("=" * 70)
    print()

    # Method 1: HTTP Authentication (v2.0 - RECOMMENDED)
    print("Method 1: HTTP Authentication (v2.0) - RECOMMENDED")
    print("-" * 70)
    username = os.getenv('TV_USERNAME')
    password = os.getenv('TV_PASSWORD')
    totp_secret = os.getenv('TV_TOTP_SECRET')

    if username and password:
        try:
            tv = TvDatafeed(
                username=username,
                password=password,
                totp_secret=totp_secret
            )
            print("✓ HTTP auth successful - reCAPTCHA bypassed automatically!")
            df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=5)
            print(f"✓ Retrieved {len(df)} bars")
        except Exception as e:
            print(f"✗ Failed: {e}")
    else:
        print("⚠ Credentials not configured")

    print()

    # Method 2: JWT Token (legacy)
    print("Method 2: JWT Token Authentication (Legacy)")
    print("-" * 70)
    auth_token = os.getenv('TV_AUTH_TOKEN')

    if auth_token:
        try:
            tv = TvDatafeed(auth_token=auth_token)
            print("✓ Token auth successful")
            df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=5)
            print(f"✓ Retrieved {len(df)} bars")
        except Exception as e:
            print(f"✗ Failed: {e}")
    else:
        print("⚠ Token not configured")

    print()

    # Method 3: No authentication
    print("Method 3: No Authentication (Limited Access)")
    print("-" * 70)
    try:
        tv = TvDatafeed()
        print("✓ Connected in no-auth mode")
        df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=5)
        print(f"✓ Retrieved {len(df)} bars (limited data)")
    except Exception as e:
        print(f"✗ Failed: {e}")

    print()
    print("Recommendation: Use Method 1 (HTTP auth) for best experience!")
    print()


def print_totp_setup_guide():
    """Print instructions for setting up TOTP for 2FA"""
    print("""
┌──────────────────────────────────────────────────────────────────┐
│                    HOW TO GET YOUR TOTP SECRET                   │
└──────────────────────────────────────────────────────────────────┘

1. Go to TradingView.com → Settings → Security
2. Navigate to "Two-factor authentication"
3. If 2FA is not enabled:
   - Click "Enable"
   - When shown the QR code, click "Can't scan?"
   - Copy the secret key (e.g., "JBSWY3DPEHPK3PXP")

4. If 2FA is already enabled:
   - You may need to disable and re-enable to see the secret
   - OR use a backup code if available

5. Save the secret in your .env file:
   TV_TOTP_SECRET=JBSWY3DPEHPK3PXP

IMPORTANT:
- Keep this secret secure (treat it like a password)
- This enables automatic 2FA code generation
- The library uses 'pyotp' to generate codes automatically

""")


def print_http_auth_advantages():
    """Print the advantages of the new HTTP auth method"""
    print("""
┌──────────────────────────────────────────────────────────────────┐
│          WHY HTTP AUTHENTICATION (v2.0) IS BETTER                │
└──────────────────────────────────────────────────────────────────┘

✅ Automatically bypasses reCAPTCHA
   No more "locked out" errors or manual token extraction!

✅ Simple username/password authentication
   Just like logging in normally - no browser required

✅ Automatic 2FA support
   Provide your TOTP secret and codes are generated automatically

✅ Works in headless environments
   Perfect for servers, Docker, CI/CD, cron jobs

✅ More reliable
   Uses HTTP requests instead of browser automation

✅ Faster authentication
   No browser startup overhead

HOW IT WORKS:
-------------
1. Sends HTTP POST to TradingView's login endpoint
2. Receives session cookies (sessionid, sessionid_sign)
3. If 2FA required, generates TOTP code and submits automatically
4. Extracts auth_token from HTML response using regex
5. Uses token for WebSocket connections

TECHNICAL DETAILS:
------------------
- Implementation: tvDatafeed/auth.py (TradingViewAuth class)
- User-Agent: TWAPI/3.0 (mimics API clients)
- Based on: dovudo/tradingview-websocket JavaScript project
- No browser fingerprinting detection

""")


def main():
    """Main function to run all examples"""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║          TvDatafeed v2.0 - HTTP Authentication Examples            ║
║                                                                    ║
║  NEW in v2.0: Automatic reCAPTCHA bypass with HTTP authentication! ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
""")

    # Load environment variables
    load_env()

    # Show advantages
    print_http_auth_advantages()

    input("Press Enter to start examples...")
    print()

    # Run examples
    example_1_basic_auth()
    input("\nPress Enter to continue...")
    print()

    example_2_with_2fa()
    input("\nPress Enter to continue...")
    print()

    example_3_production_ready()
    input("\nPress Enter to continue...")
    print()

    example_4_comparing_auth_methods()

    print("=" * 70)
    print("All examples completed!")
    print("=" * 70)
    print()
    print("For more information:")
    print("  - README.md (Authentication section)")
    print("  - CLAUDE.md (Technical documentation)")
    print("  - tvDatafeed/auth.py (Implementation)")
    print()


if __name__ == '__main__':
    main()
