# 2FA Authentication Examples

This guide shows how to use TvDatafeed with two-factor authentication.

## Prerequisites

For automatic 2FA code generation, install pyotp:

```bash
pip install pyotp
```

## Using TOTP Secret (Recommended)

The TOTP secret is shown when you first set up 2FA in TradingView.

```python
from tvDatafeed import TvDatafeed, Interval

# With TOTP secret - codes are generated automatically
tv = TvDatafeed(
    username='your_email@example.com',
    password='your_password',
    totp_secret='JBSWY3DPEHPK3PXP'  # Your base32 secret
)

# Now use normally
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=100)
print(df.head())
```

## Using Manual Code

If you don't have the TOTP secret:

```python
from tvDatafeed import TvDatafeed, Interval

# Ask user for current code
code = input("Enter your 6-digit 2FA code: ")

tv = TvDatafeed(
    username='your_email@example.com',
    password='your_password',
    totp_code=code
)

df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=100)
```

## Using Environment Variables

### Setup

Create a `.env` file:

```bash
# .env - Add to .gitignore!
TV_USERNAME=your_email@example.com
TV_PASSWORD=your_secure_password
TV_TOTP_SECRET=JBSWY3DPEHPK3PXP
```

### Usage

```python
import os
from dotenv import load_dotenv
from tvDatafeed import TvDatafeed, Interval

# Load environment variables
load_dotenv()

# Create instance - reads from environment
tv = TvDatafeed(
    username=os.getenv('TV_USERNAME'),
    password=os.getenv('TV_PASSWORD'),
    totp_secret=os.getenv('TV_TOTP_SECRET')
)

df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=100)
print(df.head())
```

## Handling 2FA Errors

### TwoFactorRequiredError

```python
from tvDatafeed import TvDatafeed, Interval
from tvDatafeed.exceptions import TwoFactorRequiredError

try:
    # Try without 2FA first
    tv = TvDatafeed(
        username='your_email@example.com',
        password='your_password'
    )
except TwoFactorRequiredError:
    print("2FA is required for this account!")

    # Option 1: Use TOTP secret
    tv = TvDatafeed(
        username='your_email@example.com',
        password='your_password',
        totp_secret='YOUR_SECRET_HERE'
    )

    # Option 2: Ask for manual code
    # code = input("Enter 2FA code: ")
    # tv = TvDatafeed(
    #     username='your_email@example.com',
    #     password='your_password',
    #     totp_code=code
    # )

# Now use normally
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=100)
```

### Invalid Code Error

```python
from tvDatafeed import TvDatafeed, Interval
from tvDatafeed.exceptions import AuthenticationError

try:
    tv = TvDatafeed(
        username='your_email@example.com',
        password='your_password',
        totp_code='wrong_code'
    )
except AuthenticationError as e:
    if 'Invalid 2FA code' in str(e):
        print("The 2FA code was invalid or expired!")
        print("Tips:")
        print("  - Ensure your device time is synchronized")
        print("  - TOTP codes expire every 30 seconds")
        print("  - Double-check your TOTP secret")
    else:
        raise
```

## Generating TOTP Codes Programmatically

If you have pyotp installed:

```python
import pyotp

# Your TOTP secret from TradingView
secret = 'JBSWY3DPEHPK3PXP'

# Create TOTP object
totp = pyotp.TOTP(secret)

# Get current code
code = totp.now()
print(f"Current 2FA code: {code}")

# Verify a code
is_valid = totp.verify('123456')
print(f"Code valid: {is_valid}")

# Get remaining time for current code
import time
remaining = 30 - (int(time.time()) % 30)
print(f"Code expires in: {remaining} seconds")
```

## Complete Example with Error Handling

```python
import os
import sys
from dotenv import load_dotenv
from tvDatafeed import TvDatafeed, Interval
from tvDatafeed.exceptions import (
    AuthenticationError,
    TwoFactorRequiredError,
    CaptchaRequiredError,
    ConfigurationError
)

def create_authenticated_client():
    """Create an authenticated TvDatafeed client."""

    # Load environment variables
    load_dotenv()

    username = os.getenv('TV_USERNAME')
    password = os.getenv('TV_PASSWORD')
    totp_secret = os.getenv('TV_TOTP_SECRET')

    # Validate credentials
    if not username or not password:
        print("Error: TV_USERNAME and TV_PASSWORD must be set")
        sys.exit(1)

    try:
        tv = TvDatafeed(
            username=username,
            password=password,
            totp_secret=totp_secret
        )
        print("Authentication successful!")
        return tv

    except TwoFactorRequiredError:
        if not totp_secret:
            print("Error: 2FA required but TV_TOTP_SECRET not set")
            print("Please set TV_TOTP_SECRET in your .env file")
            sys.exit(1)
        raise

    except CaptchaRequiredError as e:
        print("CAPTCHA verification required!")
        print(str(e))  # Shows workaround instructions
        sys.exit(1)

    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)

    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

# Usage
tv = create_authenticated_client()
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=100)
print(f"Got {len(df)} bars of data")
```

## Secure Storage Best Practices

### Using keyring (System Keychain)

```python
import keyring
from tvDatafeed import TvDatafeed, Interval

# Store credentials (do once)
# keyring.set_password('tvdatafeed', 'username', 'your_email@example.com')
# keyring.set_password('tvdatafeed', 'password', 'your_password')
# keyring.set_password('tvdatafeed', 'totp_secret', 'YOUR_SECRET')

# Retrieve credentials
username = keyring.get_password('tvdatafeed', 'username')
password = keyring.get_password('tvdatafeed', 'password')
totp_secret = keyring.get_password('tvdatafeed', 'totp_secret')

tv = TvDatafeed(
    username=username,
    password=password,
    totp_secret=totp_secret
)
```

### Using AWS Secrets Manager

```python
import boto3
import json
from tvDatafeed import TvDatafeed, Interval

def get_tv_credentials():
    """Get credentials from AWS Secrets Manager."""
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='tvdatafeed-credentials')
    return json.loads(response['SecretString'])

creds = get_tv_credentials()
tv = TvDatafeed(
    username=creds['username'],
    password=creds['password'],
    totp_secret=creds['totp_secret']
)
```
