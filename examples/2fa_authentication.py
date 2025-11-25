"""
Two-Factor Authentication (2FA) Example
========================================

This example demonstrates how to authenticate with TradingView when you have
2FA (Two-Factor Authentication) enabled on your account.

✅ NEW in v2.0: HTTP authentication automatically handles 2FA!
- No more reCAPTCHA blocking
- Automatic TOTP code generation and submission
- Works perfectly in headless environments

There are two methods:
1. TOTP Secret Key (Recommended) - Automatic code generation ✅ WORKS!
2. Manual 2FA Code - Provide the 6-digit code directly ✅ WORKS!
"""

import os
import logging
from tvDatafeed import TvDatafeed, Interval, TwoFactorRequiredError, AuthenticationError

# Enable logging to see detailed information
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def method_1_totp_secret():
    """
    Method 1: Automatic 2FA using TOTP Secret Key (RECOMMENDED)

    This method requires your TOTP secret key, which is shown when you
    first set up 2FA on TradingView.

    ✅ NEW in v2.0: This now works perfectly with HTTP authentication!
    The library automatically generates and submits the TOTP code.
    """
    print("\n" + "="*70)
    print("METHOD 1: Using TOTP Secret Key (Automatic) ✅ v2.0")
    print("="*70 + "\n")

    # Load from environment variables (RECOMMENDED)
    username = os.getenv('TV_USERNAME')
    password = os.getenv('TV_PASSWORD')
    totp_secret = os.getenv('TV_TOTP_SECRET')

    if not all([username, password, totp_secret]):
        print("Missing environment variables!")
        print("\nPlease set the following environment variables:")
        print("  export TV_USERNAME='your_username'")
        print("  export TV_PASSWORD='your_password'")
        print("  export TV_TOTP_SECRET='JBSWY3DPEHPK3PXP'  # Your secret key")
        print("\nOr create a .env file (see .env.example)")
        return

    try:
        print("Authenticating with TOTP secret (v2.0 HTTP method)...")
        print("✅ reCAPTCHA will be bypassed automatically!")
        tv = TvDatafeed(
            username=username,
            password=password,
            totp_secret=totp_secret
        )

        print("✅ Authentication successful! 2FA handled automatically!")

        # Test by fetching some data
        print("\nFetching test data...")
        df = tv.get_hist(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour,
            n_bars=10
        )

        print(f"Successfully retrieved {len(df)} bars of data!")
        print("\nLatest data:")
        print(df.tail(3))

    except TwoFactorRequiredError as e:
        print(f"2FA Error: {e}")
        print("\nMake sure your TOTP secret is correct.")

    except AuthenticationError as e:
        print(f"Authentication Error: {e}")

    except Exception as e:
        print(f"Unexpected Error: {type(e).__name__}: {e}")


def method_2_manual_code():
    """
    Method 2: Manual 2FA Code

    Use this method if you don't have your TOTP secret key.
    You'll need to provide the current 6-digit code from your authenticator app.
    """
    print("\n" + "="*70)
    print("METHOD 2: Using Manual 2FA Code")
    print("="*70 + "\n")

    username = os.getenv('TV_USERNAME')
    password = os.getenv('TV_PASSWORD')

    if not all([username, password]):
        print("Missing credentials!")
        print("\nPlease set the following environment variables:")
        print("  export TV_USERNAME='your_username'")
        print("  export TV_PASSWORD='your_password'")
        return

    # In a real application, you might prompt the user for the code
    totp_code = os.getenv('TV_2FA_CODE')

    if not totp_code:
        print("No 2FA code provided!")
        print("\nYou need to provide the current 6-digit code from your authenticator app.")
        print("Set the TV_2FA_CODE environment variable:")
        print("  export TV_2FA_CODE='123456'")
        print("\nNote: This code expires every 30 seconds!")
        return

    try:
        print(f"Authenticating with manual code: {totp_code[:2]}****...")
        tv = TvDatafeed(
            username=username,
            password=password,
            totp_code=totp_code
        )

        print("Authentication successful!")

        # Test by fetching some data
        print("\nFetching test data...")
        df = tv.get_hist(
            symbol='BTCUSDT',
            exchange='BINANCE',
            interval=Interval.in_1_hour,
            n_bars=10
        )

        print(f"Successfully retrieved {len(df)} bars of data!")
        print("\nLatest data:")
        print(df.tail(3))

    except AuthenticationError as e:
        print(f"Authentication Error: {e}")
        print("\nThe code might have expired. Get a fresh code from your authenticator.")

    except Exception as e:
        print(f"Unexpected Error: {type(e).__name__}: {e}")


def method_3_dotenv_file():
    """
    Method 3: Using a .env File (Production Ready)

    This method loads credentials from a .env file, which is the recommended
    approach for production applications.
    """
    print("\n" + "="*70)
    print("METHOD 3: Using .env File (Production Ready)")
    print("="*70 + "\n")

    try:
        from dotenv import load_dotenv

        # Load from .env file in the project root
        env_loaded = load_dotenv()

        if env_loaded:
            print("Loaded configuration from .env file")
        else:
            print("No .env file found - using existing environment variables")

    except ImportError:
        print("python-dotenv not installed. Install it with: pip install python-dotenv")
        print("Using existing environment variables...")

    username = os.getenv('TV_USERNAME')
    password = os.getenv('TV_PASSWORD')
    totp_secret = os.getenv('TV_TOTP_SECRET')
    auth_token = os.getenv('TV_AUTH_TOKEN')

    tv = None

    try:
        # Priority: auth_token > totp_secret > no 2FA
        if auth_token:
            print("Using pre-obtained auth token...")
            tv = TvDatafeed(auth_token=auth_token)

        elif all([username, password, totp_secret]):
            print("Using username/password with TOTP secret...")
            tv = TvDatafeed(
                username=username,
                password=password,
                totp_secret=totp_secret
            )

        elif username and password:
            print("Using username/password without 2FA...")
            tv = TvDatafeed(username=username, password=password)

        else:
            print("No credentials found - using unauthenticated access...")
            tv = TvDatafeed()

        print("Successfully initialized!\n")

        # Test connection
        print("Testing connection...")
        df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=5)
        print(f"Retrieved {len(df)} bars - Connection working!")

    except TwoFactorRequiredError as e:
        print(f"\n2FA is required but not configured!")
        print(f"\n{e}")
        print_2fa_setup_instructions()

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")


def print_2fa_setup_instructions():
    """Print instructions for setting up 2FA"""
    print("""
HOW TO SET UP 2FA AUTHENTICATION
================================

Step 1: Get your TOTP Secret Key
--------------------------------
1. Go to TradingView.com and log in
2. Navigate to: Settings > Security > Two-factor authentication
3. If not enabled: Enable it and click "Can't scan?" to see the secret key
4. If already enabled: You may need to disable and re-enable to see the secret
5. The secret looks like: JBSWY3DPEHPK3PXP (base32 encoded)

Step 2: Configure your environment
----------------------------------
Create a .env file in your project root (copy from .env.example):

    TV_USERNAME=your_email@example.com
    TV_PASSWORD=your_password
    TV_TOTP_SECRET=JBSWY3DPEHPK3PXP

Step 3: Use in your code
------------------------
    from dotenv import load_dotenv
    from tvDatafeed import TvDatafeed

    load_dotenv()

    tv = TvDatafeed(
        username=os.getenv('TV_USERNAME'),
        password=os.getenv('TV_PASSWORD'),
        totp_secret=os.getenv('TV_TOTP_SECRET')
    )

IMPORTANT SECURITY NOTES:
=========================
- Never commit your .env file to git (it's in .gitignore by default)
- Keep your TOTP secret as secure as your password
- Use environment variables in production environments
- Consider using a secrets manager for sensitive deployments
""")


def main():
    """Main function to run all examples"""
    print("""
+======================================================================+
|                                                                      |
|           TvDatafeed 2FA Authentication Examples                     |
|                                                                      |
|  This script demonstrates how to authenticate with TradingView       |
|  when Two-Factor Authentication (2FA) is enabled on your account.    |
|                                                                      |
+======================================================================+
""")

    # Check if we have any credentials
    has_creds = any([
        os.getenv('TV_USERNAME'),
        os.getenv('TV_AUTH_TOKEN'),
        os.getenv('TV_TOTP_SECRET')
    ])

    if not has_creds:
        print("No credentials detected in environment.")
        print_2fa_setup_instructions()
        return

    # Run Method 1: TOTP Secret
    method_1_totp_secret()

    input("\nPress Enter to continue to Method 2...")

    # Run Method 2: Manual Code
    method_2_manual_code()

    input("\nPress Enter to continue to Method 3...")

    # Run Method 3: .env File
    method_3_dotenv_file()

    print("\n" + "="*70)
    print("Examples completed!")
    print("="*70)
    print("\nFor more information, see:")
    print("  - README.md (Two-Factor Authentication section)")
    print("  - .env.example (example configuration)")
    print()


if __name__ == '__main__':
    main()
