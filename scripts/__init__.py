"""
Token management scripts for TvDatafeed

This package provides utilities for automated JWT token management:
- get_auth_token.py: Extract JWT token via Playwright browser automation
- token_manager.py: Manage token lifecycle (validation, caching, refresh)
"""

from .token_manager import (
    get_valid_token,
    get_token_info,
    is_token_valid,
    get_token_expiry,
    decode_jwt,
    get_cached_token,
    save_cached_token,
    refresh_token,
)

__all__ = [
    'get_valid_token',
    'get_token_info',
    'is_token_valid',
    'get_token_expiry',
    'decode_jwt',
    'get_cached_token',
    'save_cached_token',
    'refresh_token',
]
