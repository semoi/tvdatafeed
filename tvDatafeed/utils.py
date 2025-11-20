"""
Utility functions for TvDatafeed

This module provides various helper functions used throughout the library.
"""
import time
import random
import string
import logging
from typing import Callable, Any, Optional, TypeVar, List
from functools import wraps
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

T = TypeVar('T')


def generate_session_id(prefix: str = "qs", length: int = 12) -> str:
    """
    Generate a random session ID

    Parameters
    ----------
    prefix : str
        Prefix for the session ID
    length : int
        Length of random part

    Returns
    -------
    str
        Session ID in format "{prefix}_{random}"
    """
    random_str = ''.join(random.choice(string.ascii_lowercase) for _ in range(length))
    return f"{prefix}_{random_str}"


def generate_chart_session_id(length: int = 12) -> str:
    """
    Generate a chart session ID

    Parameters
    ----------
    length : int
        Length of random part

    Returns
    -------
    str
        Chart session ID
    """
    return generate_session_id(prefix="cs", length=length)


def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
) -> T:
    """
    Retry a function with exponential backoff

    Parameters
    ----------
    func : callable
        Function to retry
    max_retries : int
        Maximum number of retry attempts
    base_delay : float
        Initial delay between retries (seconds)
    max_delay : float
        Maximum delay between retries (seconds)
    exceptions : tuple
        Exceptions to catch and retry on
    on_retry : callable, optional
        Callback called on each retry: on_retry(attempt, exception)

    Returns
    -------
    any
        Result of func()

    Raises
    ------
    Exception
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            last_exception = e

            if attempt == max_retries:
                logger.error(f"All {max_retries} retry attempts failed")
                raise

            # Calculate delay with exponential backoff and jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = delay * 0.2 * (random.random() * 2 - 1)
            sleep_time = max(0, delay + jitter)

            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                f"Retrying in {sleep_time:.2f}s..."
            )

            if on_retry:
                on_retry(attempt + 1, e)

            time.sleep(sleep_time)

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


def timeout_decorator(seconds: float):
    """
    Decorator to add timeout to a function

    Note: This is a simple implementation using time.time().
    For more robust timeout handling, consider using signal (Unix)
    or threading.Timer.

    Parameters
    ----------
    seconds : float
        Timeout in seconds

    Returns
    -------
    function
        Decorated function

    Example
    -------
    >>> @timeout_decorator(5.0)
    ... def slow_function():
    ...     time.sleep(10)
    ...
    >>> slow_function()  # Raises TimeoutError after 5s
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time

            if elapsed > seconds:
                raise TimeoutError(
                    f"Function {func.__name__} exceeded timeout of {seconds}s "
                    f"(took {elapsed:.2f}s)"
                )

            return result
        return wrapper
    return decorator


def log_execution_time(func: Callable) -> Callable:
    """
    Decorator to log function execution time

    Parameters
    ----------
    func : callable
        Function to decorate

    Returns
    -------
    callable
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"{func.__name__} completed in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
            raise
    return wrapper


def mask_sensitive_data(data: str, visible_chars: int = 4, mask_char: str = '*') -> str:
    """
    Mask sensitive data (e.g., passwords, tokens)

    Parameters
    ----------
    data : str
        Data to mask
    visible_chars : int
        Number of characters to leave visible at the end
    mask_char : str
        Character to use for masking

    Returns
    -------
    str
        Masked string

    Example
    -------
    >>> mask_sensitive_data("my_secret_token_12345")
    '***************12345'
    """
    if not data or len(data) <= visible_chars:
        return mask_char * 8  # Return fixed-length mask for short strings

    masked_length = len(data) - visible_chars
    return mask_char * masked_length + data[-visible_chars:]


def format_timestamp(timestamp: float, fmt: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """
    Format Unix timestamp to human-readable string

    Parameters
    ----------
    timestamp : float
        Unix timestamp (seconds since epoch)
    fmt : str
        Format string for strftime

    Returns
    -------
    str
        Formatted timestamp
    """
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime(fmt)


def chunk_list(items: List[T], chunk_size: int) -> List[List[T]]:
    """
    Split a list into chunks

    Parameters
    ----------
    items : list
        List to split
    chunk_size : int
        Size of each chunk

    Returns
    -------
    list of list
        List of chunks

    Example
    -------
    >>> chunk_list([1, 2, 3, 4, 5], 2)
    [[1, 2], [3, 4], [5]]
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero

    Parameters
    ----------
    numerator : float
        Numerator
    denominator : float
        Denominator
    default : float
        Value to return if denominator is zero

    Returns
    -------
    float
        Result of division or default
    """
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Clamp a value between min and max

    Parameters
    ----------
    value : float
        Value to clamp
    min_value : float
        Minimum value
    max_value : float
        Maximum value

    Returns
    -------
    float
        Clamped value
    """
    return max(min_value, min(value, max_value))


class ContextTimer:
    """
    Context manager for timing code blocks

    Example
    -------
    >>> with ContextTimer("My operation"):
    ...     time.sleep(1)
    My operation took 1.00s
    """

    def __init__(self, name: str = "Operation", logger_instance: Optional[logging.Logger] = None):
        self.name = name
        self.logger = logger_instance or logger
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        elapsed = self.end_time - self.start_time

        if exc_type is None:
            self.logger.debug(f"{self.name} took {elapsed:.2f}s")
        else:
            self.logger.error(f"{self.name} failed after {elapsed:.2f}s")

    @property
    def elapsed(self) -> float:
        """Get elapsed time"""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return 0.0
