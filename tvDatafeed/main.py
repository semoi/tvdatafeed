"""
TvDatafeed - TradingView data downloader

This module provides the core functionality for fetching historical data
from TradingView using WebSocket connections.
"""
import datetime
import enum
import json
import logging
import os
import re
from typing import Optional
import pandas as pd
from websocket import create_connection
import requests

from .exceptions import (
    AuthenticationError,
    CaptchaRequiredError,
    TwoFactorRequiredError,
    WebSocketError,
    WebSocketTimeoutError,
    DataNotFoundError,
    DataValidationError,
    InvalidIntervalError,
    ConfigurationError
)

# Optional: pyotp for automatic TOTP code generation
try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False
from .validators import Validators
from .utils import (
    generate_session_id,
    generate_chart_session_id,
    mask_sensitive_data,
    retry_with_backoff
)

logger = logging.getLogger(__name__)


class Interval(enum.Enum):
    in_1_minute = "1"
    in_3_minute = "3"
    in_5_minute = "5"
    in_15_minute = "15"
    in_30_minute = "30"
    in_45_minute = "45"
    in_1_hour = "1H"
    in_2_hour = "2H"
    in_3_hour = "3H"
    in_4_hour = "4H"
    in_daily = "1D"
    in_weekly = "1W"
    in_monthly = "1M"


# Interval length mapping (interval -> seconds)
# Used for date range queries to calculate time periods
interval_len = {
    "1": 60,         # 1 minute
    "3": 180,        # 3 minutes
    "5": 300,        # 5 minutes
    "15": 900,       # 15 minutes
    "30": 1800,      # 30 minutes
    "45": 2700,      # 45 minutes
    "1H": 3600,      # 1 hour
    "2H": 7200,      # 2 hours
    "3H": 10800,     # 3 hours
    "4H": 14400,     # 4 hours
    "1D": 86400,     # 1 day
    "1W": 604800,    # 1 week
    "1M": 2592000,   # 1 month (30 days approximation)
}


class TvDatafeed:
    __sign_in_url = 'https://www.tradingview.com/accounts/signin/'
    __2fa_url = 'https://www.tradingview.com/accounts/two-factor/signin/totp/'
    __search_url = 'https://symbol-search.tradingview.com/symbol_search/?text={}&hl=1&exchange={}&lang=en&type=&domain=production'
    __ws_headers = json.dumps({"Origin": "https://data.tradingview.com"})
    __signin_headers = {'Referer': 'https://www.tradingview.com'}
    __ws_timeout = 5

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        auth_token: Optional[str] = None,
        totp_secret: Optional[str] = None,
        totp_code: Optional[str] = None,
        ws_timeout: Optional[float] = None,
        verbose: Optional[bool] = None,
    ) -> None:
        """Create TvDatafeed object

        Parameters
        ----------
        username : str, optional
            TradingView username. If not provided, limited unauthenticated access.
        password : str, optional
            TradingView password. Required if username is provided.
        auth_token : str, optional
            Pre-obtained authentication token. Use this if CAPTCHA is required.
            If provided, username/password are ignored.
        totp_secret : str, optional
            TOTP secret key for automatic 2FA code generation.
            This is the base32-encoded secret shown when setting up 2FA.
            If provided, 2FA codes are generated automatically using pyotp.
            Can also be set via TV_TOTP_SECRET environment variable.
        totp_code : str, optional
            Manual 6-digit 2FA code. Use this if you don't have the TOTP secret.
            This code expires quickly (usually 30 seconds).
            Can also be set via TV_2FA_CODE environment variable.
        ws_timeout : float, optional
            WebSocket timeout in seconds. If not provided, uses:
            1. Environment variable TV_WS_TIMEOUT if set
            2. NetworkConfig.recv_timeout if available
            3. Default value of 5 seconds
            Set to -1 for no timeout (not recommended).
        verbose : bool, optional
            Enable verbose logging. If False, only warnings and errors are shown.
            Can also be set via TV_VERBOSE environment variable.
            Priority: parameter > environment variable > default (True).
            If not specified, defaults to True (or value from TV_VERBOSE if set).

        Raises
        ------
        ConfigurationError
            If only username or only password is provided (both or neither required).
        AuthenticationError
            If authentication fails with provided credentials.
        CaptchaRequiredError
            If TradingView requires CAPTCHA verification.
        TwoFactorRequiredError
            If 2FA is required but no totp_secret or totp_code is provided.

        Examples
        --------
        >>> # Use default timeout
        >>> tv = TvDatafeed()
        >>>
        >>> # Use custom timeout
        >>> tv = TvDatafeed(ws_timeout=30.0)
        >>>
        >>> # Use environment variable
        >>> # export TV_WS_TIMEOUT=60.0
        >>> tv = TvDatafeed()  # Will use 60s from env
        >>>
        >>> # Quiet mode (production)
        >>> tv = TvDatafeed(verbose=False)
        >>>
        >>> # With 2FA using TOTP secret (recommended)
        >>> tv = TvDatafeed(
        ...     username="user@email.com",
        ...     password="your_password",
        ...     totp_secret="JBSWY3DPEHPK3PXP"  # Your TOTP secret key
        ... )
        >>>
        >>> # With 2FA using manual code
        >>> tv = TvDatafeed(
        ...     username="user@email.com",
        ...     password="your_password",
        ...     totp_code="123456"  # Current 6-digit code from authenticator
        ... )
        >>>
        >>> # Using environment variables for 2FA (recommended for security)
        >>> # Set in .env file or export:
        >>> # TV_USERNAME=user@email.com
        >>> # TV_PASSWORD=your_password
        >>> # TV_TOTP_SECRET=JBSWY3DPEHPK3PXP
        >>> from dotenv import load_dotenv
        >>> load_dotenv()
        >>> tv = TvDatafeed(
        ...     username=os.getenv('TV_USERNAME'),
        ...     password=os.getenv('TV_PASSWORD'),
        ...     totp_secret=os.getenv('TV_TOTP_SECRET')
        ... )
        """
        self.ws_debug = False

        # Configure verbose logging
        # Priority: parameter > environment variable > default (True)
        if verbose is not None:
            # Parameter explicitly provided, use it
            self.verbose = verbose
        else:
            # No parameter, check environment variable
            env_verbose = os.getenv('TV_VERBOSE')
            if env_verbose is not None:
                # Environment variable exists, parse it
                self.verbose = env_verbose.lower() in ('true', '1', 'yes', 'on')
            else:
                # No env var either, use default
                self.verbose = True

        # Configure logging level based on verbose setting
        if not self.verbose:
            # Quiet mode: only show warnings and errors
            logger.setLevel(logging.WARNING)
        else:
            # Verbose mode: show info and above
            logger.setLevel(logging.INFO)

        # Configure WebSocket timeout
        if ws_timeout is not None:
            # Explicit parameter takes priority
            self.ws_timeout = Validators.validate_timeout(ws_timeout)
            logger.info(f"Using WebSocket timeout: {self.ws_timeout}s (from parameter)")
        else:
            # Try environment variable
            env_timeout = os.getenv('TV_WS_TIMEOUT')
            if env_timeout:
                try:
                    self.ws_timeout = Validators.validate_timeout(float(env_timeout))
                    logger.info(f"Using WebSocket timeout: {self.ws_timeout}s (from TV_WS_TIMEOUT)")
                except (ValueError, ConfigurationError) as e:
                    logger.warning(f"Invalid TV_WS_TIMEOUT value: {e}. Using default.")
                    self.ws_timeout = self.__ws_timeout
            else:
                # Try NetworkConfig
                try:
                    from .config import NetworkConfig
                    config = NetworkConfig.from_env()
                    self.ws_timeout = config.recv_timeout
                    logger.info(f"Using WebSocket timeout: {self.ws_timeout}s (from NetworkConfig)")
                except (ImportError, Exception):
                    # Fall back to default
                    self.ws_timeout = self.__ws_timeout
                    logger.debug(f"Using default WebSocket timeout: {self.ws_timeout}s")

        # Configure 2FA settings
        # Priority: parameter > environment variable
        self._totp_secret = totp_secret or os.getenv('TV_TOTP_SECRET')
        self._totp_code = totp_code or os.getenv('TV_2FA_CODE')

        # If auth_token is provided directly, use it
        if auth_token:
            logger.info("Using pre-obtained authentication token")
            self.token = auth_token
        else:
            # Validate credentials
            Validators.validate_credentials(username, password)

            self.token = self.__auth(username, password)

            if self.token is None:
                self.token = "unauthorized_user_token"
                logger.warning(
                    "Using unauthenticated access - data may be limited. "
                    "Provide username and password for full access."
                )

        self.ws = None
        self.session = generate_session_id(prefix="qs")
        self.chart_session = generate_chart_session_id()

    def _get_totp_code(self) -> Optional[str]:
        """Generate or retrieve the 2FA code

        Returns
        -------
        str or None
            6-digit TOTP code if available, None otherwise

        Raises
        ------
        ConfigurationError
            If totp_secret is invalid or pyotp is not installed
        """
        # First, try to use the manual code if provided
        if self._totp_code:
            logger.debug("Using manually provided 2FA code")
            return self._totp_code

        # Then, try to generate from TOTP secret
        if self._totp_secret:
            if not PYOTP_AVAILABLE:
                raise ConfigurationError(
                    "totp_secret",
                    "***",
                    "pyotp library is required for automatic 2FA. "
                    "Install it with: pip install pyotp"
                )

            try:
                # Clean the secret (remove spaces, convert to uppercase)
                secret = self._totp_secret.replace(' ', '').upper()
                totp = pyotp.TOTP(secret)
                code = totp.now()
                logger.debug(f"Generated TOTP code: {code[:2]}****")
                return code
            except Exception as e:
                raise ConfigurationError(
                    "totp_secret",
                    "***",
                    f"Invalid TOTP secret: {e}. "
                    f"Ensure the secret is a valid base32-encoded string."
                )

        return None

    def __auth(self, username: Optional[str], password: Optional[str]) -> Optional[str]:
        """Authenticate with TradingView

        Parameters
        ----------
        username : str, optional
            TradingView username
        password : str, optional
            TradingView password

        Returns
        -------
        str or None
            Authentication token if successful, None for unauthenticated access

        Raises
        ------
        AuthenticationError
            If authentication fails with provided credentials
        TwoFactorRequiredError
            If 2FA is required but not provided
        """
        if username is None or password is None:
            return None

        # Use a session to maintain cookies across requests (needed for 2FA)
        session = requests.Session()

        data = {
            "username": username,
            "password": password,
            "remember": "on"
        }

        try:
            logger.info(f"Authenticating user: {username}")

            response = session.post(
                url=self.__sign_in_url,
                data=data,
                headers=self.__signin_headers,
                timeout=10.0
            )

            if response.status_code != 200:
                logger.error(f"Authentication failed with status code: {response.status_code}")
                raise AuthenticationError(
                    f"Authentication failed: HTTP {response.status_code}. "
                    f"Please check your credentials."
                )

            response_data = response.json()

            if 'error' in response_data:
                error_msg = response_data.get('error', 'Unknown error')
                error_code = response_data.get('code', '')

                logger.error(f"Authentication error: {error_msg} (code: {error_code})")

                # Check for CAPTCHA requirement
                if error_code == 'recaptcha_required':
                    raise CaptchaRequiredError(username=username)

                raise AuthenticationError(f"Authentication failed: {error_msg}")

            # Check if 2FA is required
            # TradingView returns this when 2FA is enabled on the account
            if response_data.get('two_factor_required') or response_data.get('2fa_required'):
                logger.info("Two-factor authentication required")
                return self.__handle_2fa(session, username, response_data)

            if 'user' not in response_data or 'auth_token' not in response_data['user']:
                logger.error("Invalid response structure from authentication")
                raise AuthenticationError(
                    "Authentication failed: Invalid response from server"
                )

            token = response_data['user']['auth_token']
            logger.info(f"Authentication successful for user: {username}")
            logger.debug(f"Auth token: {mask_sensitive_data(token)}")

            return token

        except requests.exceptions.Timeout:
            logger.error("Authentication request timed out")
            raise AuthenticationError(
                "Authentication timed out. Please check your network connection."
            )
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error during authentication: {e}")
            raise AuthenticationError(
                "Unable to connect to TradingView. Please check your network connection."
            )
        except AuthenticationError:
            # Re-raise our custom exceptions
            raise
        except CaptchaRequiredError:
            # Re-raise our custom exceptions
            raise
        except TwoFactorRequiredError:
            # Re-raise our custom exceptions
            raise
        except ConfigurationError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            raise AuthenticationError(
                f"Authentication failed with unexpected error: {type(e).__name__}: {e}"
            )

    def __handle_2fa(
        self,
        session: requests.Session,
        username: str,
        initial_response: dict
    ) -> str:
        """Handle two-factor authentication

        Parameters
        ----------
        session : requests.Session
            The session with cookies from initial login
        username : str
            TradingView username (for error messages)
        initial_response : dict
            The response from the initial login attempt

        Returns
        -------
        str
            Authentication token after successful 2FA

        Raises
        ------
        TwoFactorRequiredError
            If no 2FA code is available
        AuthenticationError
            If 2FA verification fails
        """
        # Get the 2FA code
        totp_code = self._get_totp_code()

        if not totp_code:
            logger.error("2FA required but no code available")
            raise TwoFactorRequiredError(method="totp")

        logger.info("Submitting 2FA code")

        # Prepare 2FA request
        data_2fa = {
            "code": totp_code,
            "remember": "on"
        }

        try:
            response_2fa = session.post(
                url=self.__2fa_url,
                data=data_2fa,
                headers=self.__signin_headers,
                timeout=10.0
            )

            if response_2fa.status_code != 200:
                logger.error(f"2FA request failed with status code: {response_2fa.status_code}")
                raise AuthenticationError(
                    f"2FA verification failed: HTTP {response_2fa.status_code}"
                )

            response_data = response_2fa.json()

            if 'error' in response_data:
                error_msg = response_data.get('error', 'Unknown error')
                error_code = response_data.get('code', '')

                logger.error(f"2FA error: {error_msg} (code: {error_code})")

                if 'invalid' in error_msg.lower() or 'incorrect' in error_msg.lower():
                    raise AuthenticationError(
                        f"Invalid 2FA code. Please check your authenticator app or TOTP secret. "
                        f"Error: {error_msg}"
                    )

                raise AuthenticationError(f"2FA verification failed: {error_msg}")

            if 'user' not in response_data or 'auth_token' not in response_data['user']:
                logger.error("Invalid response structure from 2FA verification")
                raise AuthenticationError(
                    "2FA verification failed: Invalid response from server"
                )

            token = response_data['user']['auth_token']
            logger.info(f"2FA authentication successful for user: {username}")
            logger.debug(f"Auth token: {mask_sensitive_data(token)}")

            return token

        except requests.exceptions.Timeout:
            logger.error("2FA request timed out")
            raise AuthenticationError(
                "2FA verification timed out. Please check your network connection."
            )
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error during 2FA: {e}")
            raise AuthenticationError(
                "Unable to connect to TradingView for 2FA. Please check your network connection."
            )

    def __create_connection(self) -> None:
        """Create WebSocket connection to TradingView

        Raises
        ------
        WebSocketError
            If connection cannot be established
        WebSocketTimeoutError
            If connection times out

        Notes
        -----
        Uses the timeout configured in __init__(). Default is 5 seconds,
        but can be customized via ws_timeout parameter or TV_WS_TIMEOUT environment variable.
        """
        try:
            logger.debug(f"Creating WebSocket connection to TradingView (timeout: {self.ws_timeout}s)")

            self.ws = create_connection(
                "wss://data.tradingview.com/socket.io/websocket",
                headers=self.__ws_headers,
                timeout=self.ws_timeout if self.ws_timeout != -1 else None
            )

            logger.debug("WebSocket connection established successfully")

        except TimeoutError as e:
            logger.error(f"WebSocket connection timed out after {self.ws_timeout}s")
            raise WebSocketTimeoutError(
                f"Connection to TradingView timed out after {self.ws_timeout} seconds. "
                f"Try again or increase timeout with ws_timeout parameter or TV_WS_TIMEOUT env variable."
            ) from e
        except ConnectionError as e:
            logger.error(f"WebSocket connection error: {e}")
            raise WebSocketError(
                f"Failed to connect to TradingView: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error creating WebSocket connection: {e}")
            raise WebSocketError(
                f"WebSocket connection failed: {type(e).__name__}: {e}"
            ) from e

    @staticmethod
    def __filter_raw_message(text):
        try:
            found = re.search('"m":"(.+?)",', text).group(1)
            found2 = re.search('"p":(.+?"}"])}', text).group(1)

            return found, found2
        except AttributeError:
            logger.error("error in filter_raw_message")


    @staticmethod
    def __prepend_header(st):
        return "~m~" + str(len(st)) + "~m~" + st

    @staticmethod
    def __construct_message(func, param_list):
        return json.dumps({"m": func, "p": param_list}, separators=(",", ":"))

    def __create_message(self, func, paramList):
        return self.__prepend_header(self.__construct_message(func, paramList))

    def __send_message(self, func, args):
        m = self.__create_message(func, args)
        if self.ws_debug:
            print(m)
        self.ws.send(m)

    @staticmethod
    def __create_df(
        raw_data: str,
        symbol: str,
        interval_len: Optional[int] = None,
        time_zone: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Create pandas DataFrame from raw WebSocket data

        Parameters
        ----------
        raw_data : str
            Raw WebSocket response data
        symbol : str
            Symbol name for the DataFrame
        interval_len : int, optional
            Interval length in seconds (for timezone-aware data)
        time_zone : str, optional
            Timezone name (e.g., 'America/New_York', 'UTC')
            If provided, adds timezone metadata to the DataFrame

        Returns
        -------
        pd.DataFrame or None
            DataFrame with OHLCV data, or None if parsing fails

        Notes
        -----
        The DataFrame includes columns: symbol, datetime (index), open,
        high, low, close, volume. If time_zone is provided, timezone
        information is added to the DataFrame metadata.
        """
        try:
            out = re.search(r'"s":\[(.+?)\}\]', raw_data).group(1)
            x = out.split(',{"')
            data = list()
            volume_data = True

            for xi in x:
                xi = re.split(r"\[|:|,|\]", xi)
                ts = datetime.datetime.fromtimestamp(float(xi[4]))

                row = [ts]

                for i in range(5, 10):

                    # skip converting volume data if does not exists
                    if not volume_data and i == 9:
                        row.append(0.0)
                        continue
                    try:
                        row.append(float(xi[i]))

                    except ValueError:
                        volume_data = False
                        row.append(0.0)
                        logger.debug('no volume data')

                data.append(row)

            df = pd.DataFrame(
                data, columns=["datetime", "open",
                               "high", "low", "close", "volume"]
            ).set_index("datetime")
            df.insert(0, "symbol", value=symbol)

            # Add timezone metadata if provided
            if time_zone:
                df.attrs['timezone'] = time_zone
                logger.debug(f"Added timezone metadata: {time_zone}")

            return df
        except AttributeError:
            logger.error("no data, please check the exchange and symbol")
            return None

    @staticmethod
    def is_valid_date_range(
        start: datetime.datetime,
        end: datetime.datetime
    ) -> bool:
        """
        Validate date range for historical data query

        Parameters
        ----------
        start : datetime
            Start date/time for the query
        end : datetime
            End date/time for the query

        Returns
        -------
        bool
            True if the date range is valid, False otherwise

        Notes
        -----
        A valid date range must satisfy:
        - Start date is before end date
        - Neither date is in the future
        - Both dates are after 2000-01-01
        - Dates can be timezone-aware or naive

        Examples
        --------
        >>> from datetime import datetime
        >>> TvDatafeed.is_valid_date_range(
        ...     datetime(2024, 1, 1),
        ...     datetime(2024, 1, 31)
        ... )
        True
        >>> TvDatafeed.is_valid_date_range(
        ...     datetime(2024, 1, 31),
        ...     datetime(2024, 1, 1)
        ... )
        False
        """
        # Get current time
        now = datetime.datetime.now()

        # Check if start is before end
        if start >= end:
            logger.warning(f"Invalid date range: start ({start}) must be before end ({end})")
            return False

        # Check if dates are not in the future
        if start > now:
            logger.warning(f"Invalid date range: start date ({start}) is in the future")
            return False

        if end > now:
            logger.warning(f"Invalid date range: end date ({end}) is in the future")
            return False

        # Check if dates are after 2000-01-01 (TradingView data limitation)
        min_date = datetime.datetime(2000, 1, 1)
        if start < min_date:
            logger.warning(f"Invalid date range: start date ({start}) is before 2000-01-01")
            return False

        if end < min_date:
            logger.warning(f"Invalid date range: end date ({end}) is before 2000-01-01")
            return False

        return True

    @staticmethod
    def __format_symbol(symbol, exchange, contract: int = None):
        """
        Format symbol to TradingView format

        Parameters
        ----------
        symbol : str
            Symbol name. Can be "SYMBOL" or "EXCHANGE:SYMBOL"
        exchange : str
            Exchange name (used if symbol doesn't contain exchange)
        contract : int, optional
            Futures contract number (1=front month, 2=next month, etc.)

        Returns
        -------
        str
            Formatted symbol in TradingView format

        Notes
        -----
        - If symbol already contains ":", the exchange is extracted from it
        - If symbol doesn't contain ":", the provided exchange is prepended
        - Logs info when exchange is auto-detected from symbol
        """

        # Symbol already formatted with exchange (e.g., "BINANCE:BTCUSDT")
        if ":" in symbol:
            # Extract exchange from symbol for logging
            detected_exchange = symbol.split(':')[0]
            if detected_exchange != exchange:
                logger.info(
                    f"Symbol '{symbol}' already contains exchange '{detected_exchange}'. "
                    f"Ignoring provided exchange parameter '{exchange}'."
                )
            # Use symbol as-is
            return symbol

        # Format symbol with exchange
        if contract is None:
            symbol = f"{exchange}:{symbol}"

        elif isinstance(contract, int):
            symbol = f"{exchange}:{symbol}{contract}!"

        else:
            raise ValueError("not a valid contract")

        logger.debug(f"Formatted symbol: {symbol}")
        return symbol

    def __get_response(self) -> str:
        """
        Read WebSocket responses until series_completed message is received

        Returns
        -------
        str
            Concatenated raw data from WebSocket responses

        Raises
        ------
        WebSocketTimeoutError
            If timeout occurs while receiving data
        WebSocketError
            If any other error occurs during data reception

        Notes
        -----
        This method reads messages from the WebSocket connection until it
        receives a message containing "series_completed", which indicates
        that all historical data has been transmitted.
        """
        raw_data = ""

        logger.debug("Reading WebSocket responses until series_completed")

        while True:
            try:
                result = self.ws.recv()
                raw_data = raw_data + result + "\n"
            except TimeoutError as e:
                logger.error("Timeout while receiving WebSocket data")
                raise WebSocketTimeoutError(
                    f"Timeout while fetching data. "
                    f"Try again or increase timeout."
                ) from e
            except Exception as e:
                logger.error(f"Error receiving WebSocket data: {e}")
                raise WebSocketError(
                    f"Error receiving data: {type(e).__name__}: {e}"
                ) from e

            if "series_completed" in result:
                logger.debug("Received series_completed message")
                break

        return raw_data

    def get_hist(
        self,
        symbol: str,
        exchange: str = "NSE",
        interval: Interval = Interval.in_daily,
        n_bars: Optional[int] = None,
        fut_contract: Optional[int] = None,
        extended_session: bool = False,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> Optional[pd.DataFrame]:
        """Get historical OHLCV data from TradingView

        Parameters
        ----------
        symbol : str
            Symbol name (e.g., 'BTCUSDT', 'AAPL')
        exchange : str, optional
            Exchange name (e.g., 'BINANCE', 'NASDAQ'). Not required if symbol
            is in format 'EXCHANGE:SYMBOL'. Defaults to 'NSE'.
        interval : Interval, optional
            Chart interval. Defaults to Interval.in_daily.
        n_bars : int, optional
            Number of bars to download (max 5000). Mutually exclusive with
            start_date/end_date. If not provided, must use start_date/end_date.
        fut_contract : int, optional
            Futures contract: None for cash, 1 for continuous current contract,
            2 for continuous next contract. Defaults to None.
        extended_session : bool, optional
            Regular session if False, extended session if True. Defaults to False.
        start_date : datetime, optional
            Start date for historical data query. Mutually exclusive with n_bars.
            Must be used together with end_date. Can be timezone-aware or naive.
        end_date : datetime, optional
            End date for historical data query. Mutually exclusive with n_bars.
            Must be used together with start_date. Can be timezone-aware or naive.

        Returns
        -------
        pd.DataFrame or None
            DataFrame with columns: symbol, datetime (index), open, high, low, close, volume
            If start_date/end_date used, DataFrame includes timezone metadata in df.attrs.
            Returns None if no data is available.

        Raises
        ------
        DataValidationError
            If symbol, exchange, n_bars, or date range are invalid
            If both n_bars and date range are provided
            If only one of start_date/end_date is provided
        InvalidIntervalError
            If interval is not supported
        WebSocketError
            If WebSocket connection fails
        DataNotFoundError
            If no data is available for the requested symbol

        Examples
        --------
        >>> # Using n_bars (traditional method)
        >>> tv = TvDatafeed()
        >>> df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=100)
        >>> print(df.head())
        >>>
        >>> # Using date range (new method)
        >>> from datetime import datetime
        >>> df = tv.get_hist(
        ...     'BTCUSDT', 'BINANCE', Interval.in_1_hour,
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 1, 31)
        ... )
        >>> print(df.head())
        >>> print(f"Timezone: {df.attrs.get('timezone', 'Not set')}")

        Notes
        -----
        - n_bars and date range (start_date/end_date) are mutually exclusive
        - Date range validation: start < end, no future dates, after 2000-01-01
        - TradingView API applies a -30min adjustment to timestamps internally
        - Timezone information is preserved in df.attrs when using date ranges
        """
        # Validate inputs
        symbol = Validators.validate_symbol(symbol, allow_formatted=True)
        exchange = Validators.validate_exchange(exchange)

        # Validate interval
        if not isinstance(interval, Interval):
            raise InvalidIntervalError(
                f"Invalid interval type: {type(interval).__name__}. "
                f"Must be an Interval enum value."
            )

        # Validate n_bars and date range mutual exclusivity
        using_date_range = start_date is not None or end_date is not None
        using_n_bars = n_bars is not None

        if using_date_range and using_n_bars:
            raise DataValidationError(
                "n_bars/date_range",
                f"n_bars={n_bars}, start_date={start_date}, end_date={end_date}",
                "n_bars and date range (start_date/end_date) are mutually exclusive. "
                "Use either n_bars OR start_date/end_date, not both."
            )

        if not using_date_range and not using_n_bars:
            # Default to n_bars=10 for backward compatibility
            n_bars = 10
            using_n_bars = True
            logger.debug("No n_bars or date range provided, defaulting to n_bars=10")

        # If using date range, validate both dates are provided
        if using_date_range:
            if start_date is None or end_date is None:
                raise DataValidationError(
                    "date_range",
                    f"start_date={start_date}, end_date={end_date}",
                    "Both start_date and end_date must be provided together"
                )

            # Validate date range
            if not self.is_valid_date_range(start_date, end_date):
                raise DataValidationError(
                    "date_range",
                    f"start={start_date}, end={end_date}",
                    "Invalid date range. Check that: start < end, no future dates, "
                    "dates after 2000-01-01"
                )

            # Convert datetime to Unix timestamp (milliseconds)
            # TradingView API uses milliseconds since epoch
            start_timestamp = int(start_date.timestamp() * 1000)
            end_timestamp = int(end_date.timestamp() * 1000)

            # Apply TradingView API adjustment (-30 minutes = -1800000 ms)
            # This is required by TradingView's API for date range queries
            TRADINGVIEW_TIMESTAMP_ADJUSTMENT_MS = 1800000
            start_timestamp -= TRADINGVIEW_TIMESTAMP_ADJUSTMENT_MS
            end_timestamp -= TRADINGVIEW_TIMESTAMP_ADJUSTMENT_MS

            logger.debug(
                f"Date range: {start_date} to {end_date} "
                f"(timestamps: {start_timestamp} to {end_timestamp})"
            )

        # If using n_bars, validate it
        if using_n_bars:
            n_bars = Validators.validate_n_bars(n_bars)

        symbol = self.__format_symbol(
            symbol=symbol, exchange=exchange, contract=fut_contract
        )

        interval = interval.value

        self.__create_connection()

        self.__send_message("set_auth_token", [self.token])
        self.__send_message("chart_create_session", [self.chart_session, ""])
        self.__send_message("quote_create_session", [self.session])
        self.__send_message(
            "quote_set_fields",
            [
                self.session,
                "ch",
                "chp",
                "current_session",
                "description",
                "local_description",
                "language",
                "exchange",
                "fractional",
                "is_tradable",
                "lp",
                "lp_time",
                "minmov",
                "minmove2",
                "original_name",
                "pricescale",
                "pro_name",
                "short_name",
                "type",
                "update_mode",
                "volume",
                "currency_code",
                "rchp",
                "rtc",
            ],
        )

        self.__send_message(
            "quote_add_symbols", [self.session, symbol,
                                  {"flags": ["force_permission"]}]
        )
        self.__send_message("quote_fast_symbols", [self.session, symbol])

        self.__send_message(
            "resolve_symbol",
            [
                self.chart_session,
                "symbol_1",
                '={"symbol":"'
                + symbol
                + '","adjustment":"splits","session":'
                + ('"regular"' if not extended_session else '"extended"')
                + "}",
            ],
        )
        # Create series with either n_bars or date range
        if using_date_range:
            # Format: "r,{start_timestamp}:{end_timestamp}"
            range_string = f"r,{start_timestamp}:{end_timestamp}"
            self.__send_message(
                "create_series",
                [self.chart_session, "s1", "s1", "symbol_1", interval, range_string],
            )
            logger.debug(
                f"Fetching data for {symbol} from {start_date} to {end_date} "
                f"at interval {interval}"
            )
        else:
            # Traditional n_bars format
            self.__send_message(
                "create_series",
                [self.chart_session, "s1", "s1", "symbol_1", interval, n_bars],
            )
            logger.debug(f"Fetching {n_bars} bars of data for {symbol} at interval {interval}")

        # Switch timezone to exchange timezone
        self.__send_message("switch_timezone", [self.chart_session, "exchange"])

        # Get WebSocket response
        try:
            raw_data = self.__get_response()
        finally:
            # Always close the WebSocket connection
            if self.ws:
                try:
                    self.ws.close()
                except Exception as e:
                    logger.warning(f"Error closing WebSocket: {e}")

        # Get interval length for timezone metadata
        interval_seconds = interval_len.get(interval)

        # Create DataFrame with timezone metadata if using date range
        if using_date_range:
            df = self.__create_df(raw_data, symbol, interval_seconds, "exchange")
        else:
            df = self.__create_df(raw_data, symbol)

        if df is None:
            logger.warning(f"No data returned for {symbol} on {exchange}")
            raise DataNotFoundError(
                f"No data available for {symbol} on {exchange}. "
                f"Please verify the symbol and exchange are correct."
            )

        logger.info(f"Successfully retrieved {len(df)} bars for {symbol}")
        return df

    def search_symbol(self, text: str, exchange: str = '') -> list:
        """Search for symbols on TradingView

        Parameters
        ----------
        text : str
            Search query (e.g., 'BTC', 'AAPL', 'NIFTY')
        exchange : str, optional
            Limit search to specific exchange (e.g., 'BINANCE', 'NASDAQ').
            Empty string searches all exchanges. Defaults to ''.

        Returns
        -------
        list
            List of dictionaries containing symbol information.
            Each dict contains: symbol, description, exchange, type, etc.
            Returns empty list if search fails or no results found.

        Raises
        ------
        DataValidationError
            If text is empty or invalid

        Examples
        --------
        >>> tv = TvDatafeed()
        >>> results = tv.search_symbol('BTC', 'BINANCE')
        >>> for r in results:
        ...     # Format for use in get_hist()
        ...     full_symbol = f"{r['exchange']}:{r['symbol']}"
        ...     print(f"{full_symbol} - {r['description']}")

        Notes
        -----
        Use the returned symbol with its exchange in get_hist():
            results = tv.search_symbol('BTC', 'BINANCE')
            symbol = f"{results[0]['exchange']}:{results[0]['symbol']}"
            data = tv.get_hist(symbol, 'BINANCE', Interval.in_1_hour)
        """
        if not text or not text.strip():
            raise DataValidationError("search_text", text, "Search text cannot be empty")

        text = text.strip()

        if exchange:
            exchange = Validators.validate_exchange(exchange)

        url = self.__search_url.format(text, exchange)

        try:
            logger.debug(f"Searching for symbol: '{text}' on exchange: '{exchange or 'ALL'}'")

            resp = requests.get(url, timeout=10.0)

            if resp.status_code != 200:
                logger.error(f"Symbol search failed with status code: {resp.status_code}")
                logger.warning(
                    f"TradingView search returned HTTP {resp.status_code}. "
                    f"Search manually on tradingview.com and use format 'EXCHANGE:SYMBOL'"
                )
                return []

            # Clean up HTML tags in response
            cleaned_text = resp.text.replace('</em>', '').replace('<em>', '')

            try:
                symbols_list = json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse symbol search response: {e}")
                logger.warning(
                    "Search response parsing failed. "
                    "Try searching manually on tradingview.com for the correct symbol format."
                )
                return []

            if not symbols_list:
                logger.warning(
                    f"No results found for '{text}' on {exchange or 'any exchange'}. "
                    f"Try a different search term or check tradingview.com."
                )
                return []

            logger.info(f"Found {len(symbols_list)} results for '{text}'")

            # Log formatted symbols for easy copy-paste
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Search results (format: EXCHANGE:SYMBOL):")
                for i, result in enumerate(symbols_list[:5], 1):  # Show first 5
                    formatted = f"{result.get('exchange', 'N/A')}:{result.get('symbol', 'N/A')}"
                    description = result.get('description', 'N/A')
                    logger.debug(f"  {i}. {formatted} - {description}")

            return symbols_list

        except requests.exceptions.Timeout:
            logger.error("Symbol search request timed out")
            logger.warning(
                "Search request timed out. Check your internet connection or try again later."
            )
            return []
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error during symbol search: {e}")
            logger.warning(
                "Connection error during search. Check your internet connection."
            )
            return []
        except Exception as e:
            logger.error(f"Unexpected error during symbol search: {e}")
            logger.warning(
                f"Unexpected error during search: {type(e).__name__}. "
                f"Try searching manually on tradingview.com."
            )
            return []

    @staticmethod
    def format_search_results(results: list, max_results: int = 10) -> str:
        """
        Format search results for display

        Parameters
        ----------
        results : list
            Results from search_symbol()
        max_results : int
            Maximum number of results to format

        Returns
        -------
        str
            Formatted string with symbols ready to use in get_hist()

        Examples
        --------
        >>> results = tv.search_symbol('BTC', 'BINANCE')
        >>> print(tv.format_search_results(results))
        """
        if not results:
            return "No results found."

        lines = [f"Found {len(results)} results (showing first {min(len(results), max_results)}):\n"]

        for i, result in enumerate(results[:max_results], 1):
            exchange = result.get('exchange', 'N/A')
            symbol = result.get('symbol', 'N/A')
            description = result.get('description', 'N/A')
            symbol_type = result.get('type', 'N/A')

            # Format for direct use in get_hist()
            full_symbol = f"{exchange}:{symbol}"

            lines.append(
                f"{i:2d}. {full_symbol:30s} | {description:40s} | Type: {symbol_type}"
            )

        lines.append(
            f"\nUsage: tv.get_hist('EXCHANGE:SYMBOL', 'EXCHANGE', interval, n_bars)"
        )
        lines.append(
            f"Example: tv.get_hist('{results[0].get('exchange')}:{results[0].get('symbol')}', "
            f"'{results[0].get('exchange')}', Interval.in_1_hour, n_bars=100)"
        )

        return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    tv = TvDatafeed()
    print(tv.get_hist("CRUDEOIL", "MCX", fut_contract=1))
    print(tv.get_hist("NIFTY", "NSE", fut_contract=1))
    print(
        tv.get_hist(
            "EICHERMOT",
            "NSE",
            interval=Interval.in_1_hour,
            n_bars=500,
            extended_session=False,
        )
    )
