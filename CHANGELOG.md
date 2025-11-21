# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Documentation
- **Comprehensive Pull Request Analysis (2025-11-21)**
  - Analyzed all 5 open PRs from rongardF/tvdatafeed upstream
  - Created detailed reports in docs/ directory:
    - PR_EXECUTIVE_SUMMARY.md - 1-page decision document
    - PR_INTEGRATION_PLAN.md - Detailed sprint planning
    - PR_ANALYSIS_REPORT.md - Full 28-page technical analysis
  - **Recommendations:**
    - ✅ INTEGRATE: PR #37 (Verbose logging) - 15min effort, P1 priority
    - ✅ INTEGRATE: PR #69 (Date range search) - 1 week effort, P2 priority
    - ⏸️ INVESTIGATE: PR #30 (2FA + Pro Data) - 3 days investigation required
    - ⏸️ INVESTIGATE: PR #73 (Rate limiting + Features) - 2 days investigation required
    - ❌ REJECT: PR #61 (Async operations) - Incompatible with threading architecture
  - **Next Steps:** Sprint 1 - Integrate PR #37, Sprint 2 - Integrate PR #69
  - **Estimated Timeline:** 4-6 weeks (28 agent-days) for full integration
  - Agent: Architecte Lead

### Fixed - GitHub Issues Resolved
- **Issue #70 - SyntaxWarning: invalid escape sequence**
  - Fixed regex patterns in `__create_df()` to use raw strings
  - Changed `'"s":\[(.+?)\}\]'` to `r'"s":\[(.+?)\}\]'`
  - Changed `"\[|:|,|\]"` to `r"\[|:|,|\]"`
  - Resolves Python 3.12+ warnings
  - Commit: cb5b17c

- **Issue #62 - Token is None due to recaptcha_required**
  - NEW: `CaptchaRequiredError` exception with detailed instructions
  - Detects `recaptcha_required` error code from TradingView
  - NEW: `auth_token` parameter for pre-obtained tokens
  - TvDatafeed(auth_token='...') bypasses CAPTCHA
  - Comprehensive workaround documentation in README
  - NEW: examples/captcha_workaround.py with complete guide
  - Tests for CAPTCHA detection and token usage
  - Commit: db8a8ed

- **Issue #63 - tv.get_hist() stopped working**
  - Enhanced symbol validation with format detection
  - Improved `__format_symbol()` with auto-detection
  - Robust `search_symbol()` never crashes on errors
  - NEW: `format_search_results()` helper method
  - NEW: Configurable WebSocket timeout via parameter
  - NEW: Environment variable support `TV_WS_TIMEOUT`
  - 3 methods to configure timeout (parameter > env > config)
  - "Symbol Format Guide" section in README
  - NEW: examples/symbol_format_guide.py (445 lines)
  - 14 new tests for symbol format and timeout
  - Commit: d96fa70

### Added
- **Verbose logging control (PR #37)**
  - NEW: `verbose` parameter in TvDatafeed.__init__()
  - Control log verbosity: verbose=False for quiet production logs
  - Environment variable support: TV_VERBOSE
  - Priority: parameter > env var > default (True)
  - Errors and warnings always shown regardless of verbose setting
  - Comprehensive documentation in README.md "Verbose Logging" section
  - NEW: examples/quiet_mode.py - Complete example with 5 use cases
  - 13 new unit tests for verbose mode functionality
  - Backward compatible: verbose=True by default (existing behavior)
  - Use cases: Development (verbose=True) vs Production (verbose=False)

- **Date Range Search (PR #69)**
  - NEW: `start_date` and `end_date` parameters in get_hist()
  - Fetch historical data by date range instead of n_bars
  - Support for datetime objects (timezone-aware or naive)
  - Automatic timestamp conversion with TradingView API adjustment
  - Mutually exclusive with n_bars parameter
  - NEW: `interval_len` dictionary - interval to seconds mapping
  - NEW: `is_valid_date_range()` static method for validation
  - NEW: `__get_response()` method - consolidated WebSocket response reading
  - Enhanced `__create_df()` with timezone and interval_len parameters
  - Timezone metadata stored in DataFrame.attrs['timezone']
  - Validation: start < end, no future dates, after 2000-01-01
  - NEW: Validators.validate_date_range() for date validation
  - NEW: Validators.validate_timestamp() for Unix timestamp validation
  - Comprehensive documentation in README.md "Date Range Search" section
  - NEW: examples/date_range_search.py - Complete examples (350+ lines)
  - 16 new unit tests for date range functionality (100% pass rate)
  - Backward compatible: n_bars still works exactly as before
  - Defaults to n_bars=10 when neither n_bars nor dates provided
  - Use cases: Backtesting with specific time periods, historical analysis

- **Custom exception hierarchy (tvDatafeed/exceptions.py)**
  - TvDatafeedError base class with context support
  - AuthenticationError, TwoFactorRequiredError for auth issues
  - WebSocketError, WebSocketTimeoutError for connection issues
  - DataError, DataNotFoundError, DataValidationError for data issues
  - InvalidOHLCError, InvalidIntervalError for validation
  - ThreadingError, LockTimeoutError, ConsumerError for concurrency
  - ConfigurationError, RateLimitError for config/rate limiting
  - All exceptions with helpful error messages and context

- **Input validation system (tvDatafeed/validators.py)**
  - Validators class with static validation methods
  - validate_symbol() - format and length checking
  - validate_exchange() - exchange name validation
  - validate_n_bars() - bounds checking (1-5000)
  - validate_interval() - interval enum validation
  - validate_ohlc() - OHLC price relationship validation
  - validate_volume() - volume non-negativity check
  - validate_credentials() - authentication credential validation
  - validate_timeout() - timeout value validation
  - All validators raise specific exceptions with clear messages

- **Utility functions (tvDatafeed/utils.py)**
  - generate_session_id() - random session ID generation
  - generate_chart_session_id() - chart session ID generation
  - retry_with_backoff() - exponential backoff with jitter
  - timeout_decorator() - function timeout decorator
  - log_execution_time() - execution time logging
  - mask_sensitive_data() - secure credential masking
  - format_timestamp() - Unix timestamp formatting
  - chunk_list() - list chunking utility
  - safe_divide() - division with zero handling
  - clamp() - value clamping utility
  - ContextTimer - context manager for timing code blocks

- **Comprehensive test infrastructure**
  - pytest configuration with coverage, markers, and timeouts
  - Unit tests for Seis, Consumer, TvDatafeed, Validators, Utils
  - Integration tests for basic workflow, live feed, error scenarios
  - 100+ test cases with full coverage
  - Mock fixtures for WebSocket and HTTP responses
  - Test markers: unit, integration, network, threading, slow
  - Test coverage reporting (.coveragerc)

- **Integration tests (tests/integration/)**
  - test_basic_workflow.py - basic data retrieval, validation, errors
  - test_live_feed_workflow.py - threading, callbacks, multiple symbols
  - test_error_scenarios.py - auth errors, WebSocket errors, validation
  - Comprehensive error scenario coverage
  - Thread safety tests
  - Large dataset handling tests

- **Configuration system (tvDatafeed/config.py)**
  - Centralized configuration with dataclasses
  - NetworkConfig, AuthConfig, DataConfig, ThreadingConfig
  - Environment variable support for all settings
  - .env.example template with all options

- **Development infrastructure**
  - requirements-dev.txt with testing and quality tools
  - .gitignore with comprehensive exclusions
  - pytest.ini with test configuration
  - CI/CD with GitHub Actions

- **GitHub Actions CI/CD**
  - Multi-OS testing (Ubuntu, Windows, macOS)
  - Multi-Python version testing (3.8, 3.9, 3.10, 3.11)
  - Automated linting (pylint, flake8, black, isort)
  - Type checking with mypy
  - Code coverage reporting to Codecov

- **Examples directory**
  - basic_usage.py - Getting started guide
  - live_feed.py - Real-time data monitoring
  - error_handling.py - Robust error handling patterns
  - examples/README.md - Complete guide

- **Documentation**
  - CONTRIBUTING.md - Comprehensive contribution guidelines
  - Improved README.md with:
    - Feature highlights and badges
    - Table of contents
    - Clear authentication examples
    - Configuration guide
    - Troubleshooting section
    - TA-Lib integration examples
  - Agent team documentation in .claude/agents/

### Changed
- **TvDatafeed class (main.py) - Major refactoring**
  - __init__() now validates credentials with Validators
  - Uses generate_session_id() from utils instead of inline code
  - Improved error messages and logging
  - __auth() completely rewritten:
    * Comprehensive error handling with AuthenticationError
    * HTTP status code checking
    * Timeout and connection error handling
    * Secure logging with mask_sensitive_data()
    * Clear error messages for troubleshooting
  - __create_connection() now raises WebSocketError/WebSocketTimeoutError
  - get_hist() improvements:
    * Input validation using Validators
    * Proper WebSocket cleanup in finally block
    * Raises DataNotFoundError when no data available
    * Enhanced logging with detailed progress messages
    * Comprehensive numpy-style docstrings with examples
  - search_symbol() improvements:
    * Input validation for search text and exchange
    * Timeout and connection error handling
    * Graceful error handling (returns empty list on errors)
    * Detailed docstrings
  - All public methods now have type hints
  - All public methods have numpy-style docstrings
  - Better resource management (WebSocket cleanup)

- **Package exports (__init__.py)**
  - Export all custom exceptions
  - Export Validators class
  - Export utility functions
  - Comprehensive __all__ list
  - Module docstring added

- **Dependencies updated**
  - pandas: 1.0.5 → >=1.3.0,<3.0.0
  - websocket-client: 0.57.0 → >=1.6.0,<2.0.0
  - requests: unversioned → >=2.28.0,<3.0.0
  - Added python-dotenv for environment variables
  - Added pyotp for future 2FA support

- **Code quality improvements**
  - Removed duplicate imports
  - Removed inline session generators (DRY principle)
  - Better separation of concerns
  - More maintainable error handling
  - Foundation for future improvements (2FA, retry logic)

### Fixed
- Requirements.txt now has proper version constraints
- WebSocket connections now properly closed in all scenarios
- Error messages are now clear and actionable
- Authentication errors no longer return None silently

### Security
- Added .env.example to guide secure credential storage
- Documentation emphasizes never hardcoding credentials
- All examples use environment variables for auth

## [2.1.0] - Previous Release

### Added
- Live data feed functionality (TvDatafeedLive)
- SEIS (Symbol-Exchange-Interval Set) class
- Consumer class for callbacks
- Threading support for real-time data

### Changed
- Removed selenium dependency
- Improved WebSocket handling

## [2.0.0] - Major Release

### Changed
- Complete rewrite removing selenium dependency
- Not backward compatible with 1.x

### Added
- Direct WebSocket connection to TradingView
- Improved performance

## [1.x.x] - Legacy Releases

See original repository for historical changes.

---

## Legend

- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` for vulnerability fixes
