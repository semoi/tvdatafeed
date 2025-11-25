"""
Quick test of the new HTTP authentication method
"""
import os
from tvDatafeed import TvDatafeed, Interval

# Load .env
from pathlib import Path
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)

username = os.getenv('TV_USERNAME')
password = os.getenv('TV_PASSWORD')
totp_secret = os.getenv('TV_TOTP_SECRET')

print("=" * 60)
print("Testing new HTTP authentication method")
print("=" * 60)
print()

print(f"Username: {username}")
print(f"TOTP Secret: {'Configured' if totp_secret else 'Not configured'}")
print()

try:
    # Test authentication with username/password + TOTP
    print("Creating TvDatafeed instance with HTTP auth...")
    tv = TvDatafeed(
        username=username,
        password=password,
        totp_secret=totp_secret
    )

    print("[OK] Authentication successful!")
    print()

    # Test data retrieval
    print("Fetching BTCUSDT data...")
    df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=10)

    print(f"[OK] Data retrieved: {len(df)} bars")
    print()
    print(df.head())
    print()

    print("=" * 60)
    print("SUCCESS! New HTTP authentication method works perfectly!")
    print("=" * 60)

except Exception as e:
    print()
    print("=" * 60)
    print("FAILED!")
    print("=" * 60)
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
