"""
Automated JWT Token Extraction for TradingView

This script uses Playwright with stealth mode to automatically log in to TradingView
and extract the JWT auth_token, bypassing the reCAPTCHA protection.

Requirements:
    pip install playwright playwright-stealth
    playwright install chromium

Usage:
    python scripts/get_auth_token.py

Environment variables required:
    TV_USERNAME: Your TradingView username
    TV_PASSWORD: Your TradingView password
    TV_TOTP_SECRET: (Optional) Your TOTP secret for 2FA

The token will be saved to .env file as TV_AUTH_TOKEN
"""

import os
import sys
import time
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        missing.append("playwright")

    try:
        from playwright_stealth import stealth, Stealth
    except ImportError:
        missing.append("playwright-stealth")

    if missing:
        print("Missing dependencies. Install with:")
        print(f"  pip install {' '.join(missing)}")
        if "playwright" in missing:
            print("  playwright install chromium")
        sys.exit(1)


def load_env():
    """Load environment variables from .env file"""
    env_file = project_root / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    os.environ.setdefault(key, value)


def get_totp_code(secret: str) -> str:
    """Generate TOTP code from secret"""
    try:
        import pyotp
        totp = pyotp.TOTP(secret.replace(' ', '').upper())
        return totp.now()
    except ImportError:
        print("Warning: pyotp not installed, cannot generate 2FA code")
        return None


def save_token_to_env(token: str):
    """Save the token to .env file"""
    env_file = project_root / '.env'

    # Read existing content
    lines = []
    token_found = False

    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith('TV_AUTH_TOKEN='):
                    lines.append(f'TV_AUTH_TOKEN="{token}"\n')
                    token_found = True
                else:
                    lines.append(line)

    # Add token if not found
    if not token_found:
        lines.append(f'\n# Auto-generated auth token (updated: {datetime.now().isoformat()})\n')
        lines.append(f'TV_AUTH_TOKEN="{token}"\n')

    # Write back
    with open(env_file, 'w') as f:
        f.writelines(lines)

    print(f"Token saved to {env_file}")


def decode_jwt_expiry(token: str) -> datetime:
    """Decode JWT to get expiry time"""
    try:
        import base64
        # JWT is base64url encoded, split by dots
        parts = token.split('.')
        if len(parts) != 3:
            return None

        # Decode payload (second part)
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded)

        if 'exp' in data:
            return datetime.fromtimestamp(data['exp'])
        return None
    except Exception as e:
        print(f"Could not decode JWT: {e}")
        return None


def extract_token_playwright(
    username: str,
    password: str,
    totp_secret: str = None,
    headless: bool = True,
    timeout: int = 60000
) -> str:
    """
    Extract JWT auth token using Playwright with stealth mode

    Args:
        username: TradingView username
        password: TradingView password
        totp_secret: Optional TOTP secret for 2FA
        headless: Run browser in headless mode
        timeout: Page timeout in milliseconds

    Returns:
        JWT auth token string
    """
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth

    token = None

    with sync_playwright() as p:
        # Launch browser with stealth settings
        browser = p.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )

        # Create context with stealth mode
        stealth = Stealth(
            navigator_webdriver=True,
            webgl_vendor=True,
            chrome_app=True,
            chrome_csi=True,
            chrome_load_times=True,
            chrome_runtime=True,
            navigator_languages=True,
            navigator_permissions=True,
            navigator_plugins=True,
            navigator_user_agent=True,
            navigator_vendor=True,
            hairline=True,
            media_codecs=True,
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
        )

        # Apply stealth to context
        stealth.apply_stealth_sync(context)

        page = context.new_page()

        page.set_default_timeout(timeout)

        try:
            print("Navigating to TradingView...")
            page.goto('https://www.tradingview.com/accounts/signin/')

            # Wait for login form
            print("Waiting for login form...")
            page.wait_for_selector('input[name="username"]', state='visible')

            # Fill credentials
            print("Entering credentials...")
            page.fill('input[name="username"]', username)
            page.fill('input[name="password"]', password)

            # Click sign in button
            print("Clicking sign in...")
            page.click('button[type="submit"]')

            # Wait for either 2FA prompt or successful login
            print("Waiting for response...")
            time.sleep(3)  # Give time for reCAPTCHA to process

            # Check for 2FA prompt
            totp_input = page.query_selector('input[name="code"]')
            if totp_input:
                print("2FA required...")
                if totp_secret:
                    code = get_totp_code(totp_secret)
                    if code:
                        print(f"Entering 2FA code: {code[:2]}****")
                        page.fill('input[name="code"]', code)
                        page.click('button[type="submit"]')
                        time.sleep(2)
                else:
                    print("ERROR: 2FA required but no TOTP secret provided")
                    return None

            # Wait for successful login (redirect to main page or charts)
            print("Waiting for login to complete...")
            try:
                page.wait_for_url('**/chart/**', timeout=15000)
            except:
                # Try navigating to chart page
                page.goto('https://www.tradingview.com/chart/')

            time.sleep(2)

            # Extract auth token from JavaScript
            print("Extracting auth token...")
            token = page.evaluate('() => window.user ? window.user.auth_token : null')

            if not token:
                # Try alternative methods
                print("Trying alternative extraction methods...")

                # Method 2: From localStorage
                token = page.evaluate('''() => {
                    try {
                        const user = JSON.parse(localStorage.getItem('user'));
                        return user ? user.auth_token : null;
                    } catch { return null; }
                }''')

            if not token:
                # Method 3: From cookies
                cookies = context.cookies()
                for cookie in cookies:
                    if 'auth' in cookie['name'].lower() and cookie['value'].startswith('eyJ'):
                        token = cookie['value']
                        break

            if token:
                print(f"Token extracted successfully!")
                print(f"Token preview: {token[:50]}...")

                # Decode expiry
                expiry = decode_jwt_expiry(token)
                if expiry:
                    print(f"Token expires: {expiry}")
                    print(f"Valid for: {expiry - datetime.now()}")
            else:
                print("ERROR: Could not extract token")

                # Debug: Check if logged in
                is_logged_in = page.evaluate('() => !!window.user')
                print(f"User logged in: {is_logged_in}")

                # Take screenshot for debugging
                screenshot_path = project_root / 'debug_screenshot.png'
                page.screenshot(path=str(screenshot_path))
                print(f"Debug screenshot saved to: {screenshot_path}")

        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")

            # Take screenshot on error
            try:
                screenshot_path = project_root / 'error_screenshot.png'
                page.screenshot(path=str(screenshot_path))
                print(f"Error screenshot saved to: {screenshot_path}")
            except:
                pass

        finally:
            browser.close()

    return token


def main():
    """Main entry point"""
    print("=" * 60)
    print("TradingView JWT Token Extractor")
    print("=" * 60)

    # Check dependencies
    check_dependencies()

    # Load environment
    load_env()

    # Get credentials
    username = os.getenv('TV_USERNAME')
    password = os.getenv('TV_PASSWORD')
    totp_secret = os.getenv('TV_TOTP_SECRET')

    if not username or not password:
        print("ERROR: TV_USERNAME and TV_PASSWORD environment variables required")
        print("Set them in .env file or export them:")
        print("  export TV_USERNAME='your_username'")
        print("  export TV_PASSWORD='your_password'")
        sys.exit(1)

    print(f"Username: {username}")
    print(f"2FA configured: {'Yes' if totp_secret else 'No'}")
    print()

    # Extract token
    # Set headless=False if you want to see the browser (useful for debugging)
    token = extract_token_playwright(
        username=username,
        password=password,
        totp_secret=totp_secret,
        headless=True  # Set to False to see the browser
    )

    if token:
        # Save to .env file
        save_token_to_env(token)

        # Also print for manual use
        print()
        print("=" * 60)
        print("TOKEN (copy this if needed):")
        print("=" * 60)
        print(token)
        print("=" * 60)

        return 0
    else:
        print()
        print("Failed to extract token. Try running with headless=False to debug.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
