# Installation

## Requirements

- Python 3.8 or higher
- pip package manager

## Install from PyPI

```bash
pip install tvdatafeed
```

## Install from Source

```bash
git clone https://github.com/semoi/tvdatafeed.git
cd tvdatafeed
pip install -e .
```

## Optional Dependencies

### 2FA Support (TOTP)

For automatic 2FA code generation:

```bash
pip install pyotp
```

### Environment Variables

For loading credentials from `.env` files:

```bash
pip install python-dotenv
```

### Development Dependencies

For contributing to TvDatafeed:

```bash
pip install -e ".[dev]"
```

This includes:
- pytest for testing
- pytest-cov for coverage
- flake8 for linting
- mypy for type checking

## Verify Installation

```python
from tvDatafeed import TvDatafeed, Interval

# Should print the version
print(TvDatafeed.__module__)

# Quick test
tv = TvDatafeed()
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_daily, n_bars=5)
print(df)
```

## Troubleshooting

### ImportError

If you get `ImportError: No module named 'tvDatafeed'`:

```bash
# Make sure you're using the correct pip
python -m pip install tvdatafeed
```

### WebSocket Connection Issues

If WebSocket connections fail:

```bash
# Install websocket-client
pip install websocket-client
```

### SSL Certificate Errors

On some systems, you may need to update certificates:

```bash
# macOS
brew install openssl

# Ubuntu/Debian
sudo apt-get install ca-certificates
```
