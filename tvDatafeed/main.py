"""
TvDatafeed - TradingView data downloader

This module provides the core functionality for fetching historical data
from TradingView using WebSocket connections.
"""
import datetime
import enum
import json
import logging
import re
from typing import Optional
import pandas as pd
from websocket import create_connection
import requests

from .exceptions import (
    AuthenticationError,
    WebSocketError,
    WebSocketTimeoutError,
    DataNotFoundError,
    DataValidationError,
    InvalidIntervalError,
    ConfigurationError
)
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


class TvDatafeed:
    __sign_in_url = 'https://www.tradingview.com/accounts/signin/'
    __search_url = 'https://symbol-search.tradingview.com/symbol_search/?text={}&hl=1&exchange={}&lang=en&type=&domain=production'
    __ws_headers = json.dumps({"Origin": "https://data.tradingview.com"})
    __signin_headers = {'Referer': 'https://www.tradingview.com'}
    __ws_timeout = 5

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        """Create TvDatafeed object

        Parameters
        ----------
        username : str, optional
            TradingView username. If not provided, limited unauthenticated access.
        password : str, optional
            TradingView password. Required if username is provided.

        Raises
        ------
        ConfigurationError
            If only username or only password is provided (both or neither required).
        AuthenticationError
            If authentication fails with provided credentials.
        """
        self.ws_debug = False

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
        """
        if username is None or password is None:
            return None

        data = {
            "username": username,
            "password": password,
            "remember": "on"
        }

        try:
            logger.info(f"Authenticating user: {username}")

            response = requests.post(
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
                logger.error(f"Authentication error: {error_msg}")
                raise AuthenticationError(f"Authentication failed: {error_msg}")

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
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            raise AuthenticationError(
                f"Authentication failed with unexpected error: {type(e).__name__}: {e}"
            )

    def __create_connection(self) -> None:
        """Create WebSocket connection to TradingView

        Raises
        ------
        WebSocketError
            If connection cannot be established
        WebSocketTimeoutError
            If connection times out
        """
        try:
            logger.debug("Creating WebSocket connection to TradingView")

            self.ws = create_connection(
                "wss://data.tradingview.com/socket.io/websocket",
                headers=self.__ws_headers,
                timeout=self.__ws_timeout
            )

            logger.debug("WebSocket connection established successfully")

        except TimeoutError as e:
            logger.error(f"WebSocket connection timed out after {self.__ws_timeout}s")
            raise WebSocketTimeoutError(
                f"Connection to TradingView timed out after {self.__ws_timeout} seconds. "
                f"Try again or increase timeout."
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
    def __create_df(raw_data, symbol):
        try:
            out = re.search('"s":\[(.+?)\}\]', raw_data).group(1)
            x = out.split(',{"')
            data = list()
            volume_data = True

            for xi in x:
                xi = re.split("\[|:|,|\]", xi)
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

            data = pd.DataFrame(
                data, columns=["datetime", "open",
                               "high", "low", "close", "volume"]
            ).set_index("datetime")
            data.insert(0, "symbol", value=symbol)
            return data
        except AttributeError:
            logger.error("no data, please check the exchange and symbol")

    @staticmethod
    def __format_symbol(symbol, exchange, contract: int = None):

        if ":" in symbol:
            pass
        elif contract is None:
            symbol = f"{exchange}:{symbol}"

        elif isinstance(contract, int):
            symbol = f"{exchange}:{symbol}{contract}!"

        else:
            raise ValueError("not a valid contract")

        return symbol

    def get_hist(
        self,
        symbol: str,
        exchange: str = "NSE",
        interval: Interval = Interval.in_daily,
        n_bars: int = 10,
        fut_contract: Optional[int] = None,
        extended_session: bool = False,
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
            Number of bars to download (max 5000). Defaults to 10.
        fut_contract : int, optional
            Futures contract: None for cash, 1 for continuous current contract,
            2 for continuous next contract. Defaults to None.
        extended_session : bool, optional
            Regular session if False, extended session if True. Defaults to False.

        Returns
        -------
        pd.DataFrame or None
            DataFrame with columns: symbol, datetime (index), open, high, low, close, volume
            Returns None if no data is available.

        Raises
        ------
        DataValidationError
            If symbol, exchange, or n_bars are invalid
        InvalidIntervalError
            If interval is not supported
        WebSocketError
            If WebSocket connection fails
        DataNotFoundError
            If no data is available for the requested symbol

        Examples
        --------
        >>> tv = TvDatafeed()
        >>> df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=100)
        >>> print(df.head())
        """
        # Validate inputs
        symbol = Validators.validate_symbol(symbol, allow_formatted=True)
        exchange = Validators.validate_exchange(exchange)
        n_bars = Validators.validate_n_bars(n_bars)

        # Validate interval
        if not isinstance(interval, Interval):
            raise InvalidIntervalError(
                f"Invalid interval type: {type(interval).__name__}. "
                f"Must be an Interval enum value."
            )

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
        self.__send_message(
            "create_series",
            [self.chart_session, "s1", "s1", "symbol_1", interval, n_bars],
        )
        self.__send_message("switch_timezone", [
                            self.chart_session, "exchange"])

        raw_data = ""

        logger.debug(f"Fetching {n_bars} bars of data for {symbol} at interval {interval}")

        try:
            while True:
                try:
                    result = self.ws.recv()
                    raw_data = raw_data + result + "\n"
                except TimeoutError as e:
                    logger.error(f"Timeout while receiving data for {symbol}")
                    raise WebSocketTimeoutError(
                        f"Timeout while fetching data for {symbol}. "
                        f"Try again or increase timeout."
                    ) from e
                except Exception as e:
                    logger.error(f"Error receiving WebSocket data: {e}")
                    raise WebSocketError(
                        f"Error receiving data: {type(e).__name__}: {e}"
                    ) from e

                if "series_completed" in result:
                    break

        finally:
            # Always close the WebSocket connection
            if self.ws:
                try:
                    self.ws.close()
                except Exception as e:
                    logger.warning(f"Error closing WebSocket: {e}")

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

        Raises
        ------
        DataValidationError
            If text is empty or invalid

        Examples
        --------
        >>> tv = TvDatafeed()
        >>> results = tv.search_symbol('BTC', 'BINANCE')
        >>> for r in results:
        ...     print(f"{r['symbol']} - {r['description']}")
        """
        if not text or not text.strip():
            raise DataValidationError("Search text cannot be empty")

        text = text.strip()

        if exchange:
            exchange = Validators.validate_exchange(exchange)

        url = self.__search_url.format(text, exchange)

        try:
            logger.debug(f"Searching for symbol: '{text}' on exchange: '{exchange or 'ALL'}'")

            resp = requests.get(url, timeout=10.0)

            if resp.status_code != 200:
                logger.error(f"Symbol search failed with status code: {resp.status_code}")
                return []

            # Clean up HTML tags in response
            cleaned_text = resp.text.replace('</em>', '').replace('<em>', '')
            symbols_list = json.loads(cleaned_text)

            logger.info(f"Found {len(symbols_list)} results for '{text}'")
            return symbols_list

        except requests.exceptions.Timeout:
            logger.error("Symbol search request timed out")
            return []
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error during symbol search: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse symbol search response: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during symbol search: {e}")
            return []


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
