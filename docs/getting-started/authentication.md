# Authentication

Authentication with TradingView provides access to more data and higher rate limits.

## Authentication Methods

### 1. Username/Password

Basic authentication with TradingView credentials:

```python
from tvDatafeed import TvDatafeed

tv = TvDatafeed(
    username='your_username',
    password='your_password'
)
```

### 2. With 2FA (TOTP Secret) - Recommended

If your account has 2FA enabled, use your TOTP secret for automatic code generation:

```python
from tvDatafeed import TvDatafeed

tv = TvDatafeed(
    username='your_username',
    password='your_password',
    totp_secret='YOUR_BASE32_SECRET'  # From authenticator setup
)
```

!!! tip "Finding Your TOTP Secret"
    The TOTP secret is shown when you first set up 2FA in TradingView.
    It's usually a base32-encoded string like `JBSWY3DPEHPK3PXP`.

### 3. With 2FA (Manual Code)

If you don't have the TOTP secret, you can provide the current code:

```python
from tvDatafeed import TvDatafeed

tv = TvDatafeed(
    username='your_username',
    password='your_password',
    totp_code='123456'  # Current 6-digit code
)
```

!!! warning "Code Expiration"
    Manual codes expire quickly (usually 30 seconds).
    Use `totp_secret` instead for automation.

### 4. Pre-obtained Auth Token

Use when CAPTCHA is required or for advanced use cases:

```python
from tvDatafeed import TvDatafeed

tv = TvDatafeed(auth_token='your_auth_token')
```

## Using Environment Variables

### Recommended Setup

Create a `.env` file (add to `.gitignore`!):

```bash
# .env
TV_USERNAME=your_email@example.com
TV_PASSWORD=your_secure_password
TV_TOTP_SECRET=YOUR_BASE32_SECRET
```

Load and use:

```python
import os
from dotenv import load_dotenv
from tvDatafeed import TvDatafeed

load_dotenv()

tv = TvDatafeed(
    username=os.getenv('TV_USERNAME'),
    password=os.getenv('TV_PASSWORD'),
    totp_secret=os.getenv('TV_TOTP_SECRET')
)
```

### Available Environment Variables

| Variable | Description |
|----------|-------------|
| `TV_USERNAME` | TradingView username |
| `TV_PASSWORD` | TradingView password |
| `TV_TOTP_SECRET` | TOTP secret for 2FA |
| `TV_2FA_CODE` | Manual 2FA code |

## Handling CAPTCHA

If TradingView requires CAPTCHA, you'll get a `CaptchaRequiredError`.

### Workaround

1. Log in to TradingView manually in your browser
2. Complete the CAPTCHA
3. Open DevTools (F12) > Application > Cookies
4. Find `authToken` cookie for tradingview.com
5. Copy the token value
6. Use it with TvDatafeed:

```python
from tvDatafeed import TvDatafeed

tv = TvDatafeed(auth_token='your_copied_auth_token')
```

## Handling 2FA Required Error

```python
from tvDatafeed import TvDatafeed
from tvDatafeed.exceptions import TwoFactorRequiredError

try:
    tv = TvDatafeed(username='user', password='pass')
except TwoFactorRequiredError:
    print("2FA required!")

    # Option 1: Provide TOTP secret
    tv = TvDatafeed(
        username='user',
        password='pass',
        totp_secret='YOUR_SECRET'
    )

    # Option 2: Ask for code
    code = input("Enter 2FA code: ")
    tv = TvDatafeed(
        username='user',
        password='pass',
        totp_code=code
    )
```

## Security Best Practices

### Do

- Store credentials in environment variables
- Use `.env` files (add to `.gitignore`)
- Use `totp_secret` instead of `totp_code` for automation
- Regularly rotate passwords

### Don't

- Hardcode credentials in source code
- Commit `.env` files to version control
- Share TOTP secrets
- Log sensitive data

### Example Secure Setup

```python
import os
import logging
from dotenv import load_dotenv
from tvDatafeed import TvDatafeed

# Configure logging to NOT show credentials
logging.basicConfig(level=logging.INFO)

# Load from environment
load_dotenv()

# Validate environment
required_vars = ['TV_USERNAME', 'TV_PASSWORD']
missing = [v for v in required_vars if not os.getenv(v)]
if missing:
    raise EnvironmentError(f"Missing: {missing}")

# Create instance
tv = TvDatafeed(
    username=os.getenv('TV_USERNAME'),
    password=os.getenv('TV_PASSWORD'),
    totp_secret=os.getenv('TV_TOTP_SECRET'),
    verbose=False  # Quiet mode for production
)

# Use it
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=100)
```

## Troubleshooting

### Invalid Credentials

```
AuthenticationError: Authentication failed: Invalid username or password
```

- Double-check username/password
- Try logging in manually on tradingview.com
- Check for typos in environment variables

### 2FA Code Invalid

```
AuthenticationError: Invalid 2FA code
```

- Ensure your device time is synchronized
- TOTP codes are time-sensitive (30-second window)
- Verify the TOTP secret is correct

### CAPTCHA Required

```
CaptchaRequiredError: TradingView requires CAPTCHA verification
```

- Log in manually and complete CAPTCHA
- Use auth_token workaround
- Wait and try again later

### Account Locked

```
AuthenticationError: Account locked
```

- Wait 15-30 minutes
- Reset password if necessary
- Contact TradingView support
