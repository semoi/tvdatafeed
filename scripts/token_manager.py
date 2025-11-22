"""
Token Manager for TradingView

Automatically manages JWT token lifecycle:
- Checks if current token is valid
- Refreshes token before expiry
- Stores token securely

Usage in your scripts:
    from scripts.token_manager import get_valid_token

    token = get_valid_token()
    tv = TvDatafeed(auth_token=token)
"""

import os
import sys
import json
import base64
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Token refresh threshold (refresh if less than this time remaining)
TOKEN_REFRESH_THRESHOLD = timedelta(hours=1)

# Token file for caching
TOKEN_CACHE_FILE = project_root / '.token_cache.json'


def load_env():
    """Load environment variables from .env file"""
    env_file = project_root / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip().strip('"').strip("'")
                    os.environ.setdefault(key, value)


def decode_jwt(token: str) -> Optional[dict]:
    """Decode JWT payload without verification"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None

        payload = parts[1]
        # Add padding
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """Get token expiration datetime"""
    payload = decode_jwt(token)
    if payload and 'exp' in payload:
        return datetime.fromtimestamp(payload['exp'])
    return None


def is_token_valid(token: str, threshold: timedelta = TOKEN_REFRESH_THRESHOLD) -> bool:
    """Check if token is valid and not expiring soon"""
    if not token or not token.startswith('eyJ'):
        return False

    expiry = get_token_expiry(token)
    if not expiry:
        return False

    # Token is valid if it expires after (now + threshold)
    return expiry > datetime.now() + threshold


def get_cached_token() -> Optional[str]:
    """Get token from cache file"""
    if TOKEN_CACHE_FILE.exists():
        try:
            with open(TOKEN_CACHE_FILE) as f:
                data = json.load(f)
                return data.get('token')
        except Exception:
            pass
    return None


def save_cached_token(token: str):
    """Save token to cache file"""
    try:
        with open(TOKEN_CACHE_FILE, 'w') as f:
            json.dump({
                'token': token,
                'updated': datetime.now().isoformat(),
                'expiry': get_token_expiry(token).isoformat() if get_token_expiry(token) else None
            }, f, indent=2)
        # Secure the file
        os.chmod(TOKEN_CACHE_FILE, 0o600)
    except Exception as e:
        print(f"Warning: Could not cache token: {e}")


def refresh_token() -> Optional[str]:
    """Get a fresh token using Playwright"""
    try:
        from scripts.get_auth_token import extract_token_playwright, load_env as load_env_script

        load_env_script()

        username = os.getenv('TV_USERNAME')
        password = os.getenv('TV_PASSWORD')
        totp_secret = os.getenv('TV_TOTP_SECRET')

        if not username or not password:
            print("ERROR: TV_USERNAME and TV_PASSWORD required for token refresh")
            return None

        print("Refreshing token via Playwright...")
        token = extract_token_playwright(
            username=username,
            password=password,
            totp_secret=totp_secret,
            headless=True
        )

        if token:
            save_cached_token(token)
            print("Token refreshed successfully")

        return token

    except ImportError as e:
        print(f"ERROR: Cannot refresh token - missing dependencies: {e}")
        print("Install with: pip install playwright playwright-stealth && playwright install chromium")
        return None


def get_valid_token(auto_refresh: bool = True) -> Optional[str]:
    """
    Get a valid auth token, refreshing if necessary

    Args:
        auto_refresh: Automatically refresh token if expired/expiring

    Returns:
        Valid JWT token or None

    Usage:
        from scripts.token_manager import get_valid_token
        from tvDatafeed import TvDatafeed

        token = get_valid_token()
        if token:
            tv = TvDatafeed(auth_token=token)
            df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour)
    """
    load_env()

    # Priority 1: Environment variable
    token = os.getenv('TV_AUTH_TOKEN')
    if token and is_token_valid(token):
        return token

    # Priority 2: Cached token
    token = get_cached_token()
    if token and is_token_valid(token):
        return token

    # Priority 3: Refresh token
    if auto_refresh:
        token = refresh_token()
        if token:
            return token

    # If we have a token but it's expiring soon, return it anyway
    # (better than nothing)
    token = os.getenv('TV_AUTH_TOKEN') or get_cached_token()
    if token:
        expiry = get_token_expiry(token)
        if expiry and expiry > datetime.now():
            print(f"Warning: Token expiring soon at {expiry}")
            return token

    return None


def get_token_info(token: str = None) -> dict:
    """Get information about a token"""
    if token is None:
        load_env()
        token = os.getenv('TV_AUTH_TOKEN') or get_cached_token()

    if not token:
        return {'valid': False, 'error': 'No token found'}

    payload = decode_jwt(token)
    if not payload:
        return {'valid': False, 'error': 'Invalid JWT format'}

    expiry = get_token_expiry(token)
    now = datetime.now()

    return {
        'valid': expiry > now if expiry else False,
        'user_id': payload.get('user_id'),
        'plan': payload.get('plan'),
        'permissions': payload.get('perm', '').split(',') if payload.get('perm') else [],
        'max_connections': payload.get('max_connections'),
        'issued_at': datetime.fromtimestamp(payload['iat']).isoformat() if 'iat' in payload else None,
        'expires_at': expiry.isoformat() if expiry else None,
        'time_remaining': str(expiry - now) if expiry else None,
        'needs_refresh': not is_token_valid(token) if expiry else True
    }


def main():
    """CLI for token management"""
    import argparse

    parser = argparse.ArgumentParser(description='TradingView Token Manager')
    parser.add_argument('--info', action='store_true', help='Show token info')
    parser.add_argument('--refresh', action='store_true', help='Force token refresh')
    parser.add_argument('--check', action='store_true', help='Check if token is valid')
    args = parser.parse_args()

    load_env()

    if args.info:
        info = get_token_info()
        print(json.dumps(info, indent=2))

    elif args.refresh:
        token = refresh_token()
        if token:
            print("Token refreshed successfully")
            info = get_token_info(token)
            print(f"Expires: {info.get('expires_at')}")
        else:
            print("Failed to refresh token")
            sys.exit(1)

    elif args.check:
        token = get_valid_token(auto_refresh=False)
        if token:
            info = get_token_info(token)
            if info['valid']:
                print(f"Token is valid. Expires: {info.get('expires_at')}")
                print(f"Time remaining: {info.get('time_remaining')}")
            else:
                print("Token is expired")
                sys.exit(1)
        else:
            print("No token found")
            sys.exit(1)

    else:
        # Default: get valid token
        token = get_valid_token()
        if token:
            print("Valid token available")
            info = get_token_info(token)
            print(f"Plan: {info.get('plan')}")
            print(f"Expires: {info.get('expires_at')}")
        else:
            print("No valid token available")
            sys.exit(1)


if __name__ == '__main__':
    main()
