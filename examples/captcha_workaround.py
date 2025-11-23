"""
CAPTCHA Workaround Example
==========================

This example demonstrates how to handle TradingView's CAPTCHA requirement
by manually extracting the authentication token from your browser.

When TradingView requires CAPTCHA verification, you'll receive a
CaptchaRequiredError with detailed instructions on how to proceed.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path for direct execution
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tvDatafeed import TvDatafeed, Interval
from tvDatafeed.exceptions import CaptchaRequiredError, AuthenticationError

# Enable logging to see detailed information
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def method_1_handle_captcha_error():
    """
    Method 1: Handle CaptchaRequiredError and follow instructions

    This is the recommended approach when you first encounter the CAPTCHA issue.
    """
    print("\n" + "="*70)
    print("METHOD 1: Handling CaptchaRequiredError")
    print("="*70 + "\n")

    try:
        # Attempt to authenticate with username/password
        tv = TvDatafeed(
            username=os.getenv('TV_USERNAME'),
            password=os.getenv('TV_PASSWORD')
        )

        # If we reach here, authentication succeeded
        print("[OK] Authentication successful!")

    except CaptchaRequiredError as e:
        print("[FAIL] CAPTCHA Required!")
        print("\nThe error message contains detailed instructions:\n")
        print(str(e))
        print("\n" + "-"*70)
        print("Follow the instructions above to extract your auth_token.")
        print("-"*70 + "\n")

    except AuthenticationError as e:
        error_msg = str(e)
        if "rate_limit" in error_msg.lower() or "locked out" in error_msg.lower():
            print("[FAIL] reCAPTCHA blocked login (shown as 'rate_limit')!")
            print("\nThis is NOT a real rate limit - it's TradingView's invisible reCAPTCHA.")
            print("Solution: Extract JWT token from browser. See Method 2.")
        else:
            print(f"[FAIL] Authentication error: {e}")


def method_2_use_token_directly():
    """
    Method 2: Use a pre-obtained authentication token

    After you've extracted the token from your browser, use this method.
    """
    print("\n" + "="*70)
    print("METHOD 2: Using Pre-obtained Token")
    print("="*70 + "\n")

    # Option 1: Load token from environment variable (RECOMMENDED)
    auth_token = os.getenv('TV_AUTH_TOKEN')

    # Option 2: Hardcode token (NOT RECOMMENDED for production)
    # auth_token = "your_token_here"

    if not auth_token:
        print("[FAIL] No auth token found!")
        print("\nPlease set the TV_AUTH_TOKEN environment variable:")
        print("  export TV_AUTH_TOKEN='your_token_here'")
        print("\nOr extract it from your browser following these steps:\n")
        print_extraction_instructions()
        return

    try:
        # Initialize with the token
        tv = TvDatafeed(auth_token=auth_token)
        print("[OK] Successfully initialized with auth_token!")

        # Test the connection by fetching some data
        print("\nTesting connection by fetching BTC data...")
        df = tv.get_hist(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour,
            n_bars=10
        )

        print(f"[OK] Successfully fetched {len(df)} bars of data!")
        print("\nLatest data:")
        print(df.tail(3))

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        print("\nYour token might be expired. Please extract a new one.")


def print_extraction_instructions():
    """Print detailed instructions for extracting the auth token"""
    print("""
HOW TO EXTRACT AUTH TOKEN FROM BROWSER
======================================

1. Open Chrome, Firefox, or any modern browser

2. Go to https://www.tradingview.com

3. Log in to your account and complete the CAPTCHA

4. Open Developer Tools:
   - Chrome: Press F12 or Ctrl+Shift+I (Cmd+Option+I on Mac)
   - Firefox: Press F12 or Ctrl+Shift+I (Cmd+Option+I on Mac)

5. Navigate to the Storage/Application tab:
   - Chrome: Click "Application" tab → "Cookies" → "https://www.tradingview.com"
   - Firefox: Click "Storage" tab → "Cookies" → "https://www.tradingview.com"

6. Find the cookie named "authToken"
   - It should be in the list of cookies
   - The value will be a long string like: "eyJhbGciOiJSUzUxMi..."

7. Copy the entire value (double-click to select all)

8. Use it in your code:

   Method A - Environment variable (SECURE):
   $ export TV_AUTH_TOKEN='paste_your_token_here'

   Method B - Direct usage (for testing only):
   tv = TvDatafeed(auth_token='paste_your_token_here')

IMPORTANT NOTES:
================
- The token is tied to your session and will expire
- If you log out or the token expires, you'll need to extract a new one
- Never share your token publicly (treat it like a password)
- Store it in environment variables or secure configuration files

TROUBLESHOOTING:
================
- If you don't see "authToken" cookie, make sure you're logged in
- If the token doesn't work, it might be expired - extract a new one
- Some browsers might show the cookie in a different format
""")


def method_3_complete_workflow():
    """
    Method 3: Complete workflow with error handling

    This demonstrates a production-ready approach with proper error handling.
    """
    print("\n" + "="*70)
    print("METHOD 3: Complete Workflow with Error Handling")
    print("="*70 + "\n")

    # Try to get credentials from environment
    username = os.getenv('TV_USERNAME')
    password = os.getenv('TV_PASSWORD')
    auth_token = os.getenv('TV_AUTH_TOKEN')
    totp_secret = os.getenv('TV_TOTP_SECRET')

    tv = None

    try:
        if auth_token:
            # Prefer token if available
            print("Using pre-obtained auth token...")
            tv = TvDatafeed(auth_token=auth_token, verbose=True)

        elif username and password:
            if totp_secret:
                # Use TOTP for 2FA
                print("Using username/password with TOTP 2FA...")
                tv = TvDatafeed(
                    username=username,
                    password=password,
                    totp_secret=totp_secret,
                    verbose=True
                )
            else:
                # Fall back to username/password
                print("Attempting authentication with username/password...")
                tv = TvDatafeed(username=username, password=password, verbose=True)

        else:
            # Use unauthenticated access
            print("No credentials provided, using unauthenticated access...")
            tv = TvDatafeed(verbose=True)

        print("[OK] Initialization successful!\n")

        # Fetch some data to test
        print("Fetching Bitcoin data...")
        df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=5)

        print(f"[OK] Retrieved {len(df)} bars")
        print("\nLatest close price:", df.iloc[-1]['close'])

    except CaptchaRequiredError as e:
        print("[FAIL] CAPTCHA verification required!\n")
        print("Follow these steps to continue:\n")
        print_extraction_instructions()

    except AuthenticationError as e:
        error_msg = str(e)
        if "rate_limit" in error_msg.lower() or "locked out" in error_msg.lower():
            print("[FAIL] reCAPTCHA blocked login (shown as 'rate_limit')!")
            print("\nThis is TradingView's invisible reCAPTCHA, not a real rate limit.")
            print("Solution: Use auth_token instead of username/password.")
            print("\nExtract token with: python scripts/get_auth_token.py")
            print("Or manually from browser console: window.user.auth_token")
        else:
            print(f"[FAIL] Authentication error: {e}")

    except Exception as e:
        print(f"[FAIL] Unexpected error: {type(e).__name__}: {e}")


def main():
    """
    Main function to run all examples
    """
    print("""
========================================================================

              TvDatafeed CAPTCHA Workaround Examples

  This script demonstrates how to handle TradingView's CAPTCHA
  requirement by manually extracting the authentication token.

========================================================================
""")

    # Run Method 1: Show what happens with CAPTCHA error
    method_1_handle_captcha_error()

    input("\nPress Enter to continue to Method 2...")

    # Run Method 2: Use pre-obtained token
    method_2_use_token_directly()

    input("\nPress Enter to continue to Method 3...")

    # Run Method 3: Complete workflow
    method_3_complete_workflow()

    print("\n" + "="*70)
    print("Examples completed!")
    print("="*70)
    print("\nFor more information, see:")
    print("  - README.md (CAPTCHA Workaround section)")
    print("  - https://github.com/rongardF/tvdatafeed/issues/62")
    print()


if __name__ == '__main__':
    main()
