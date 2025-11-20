# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Comprehensive test infrastructure**
  - pytest configuration with coverage, markers, and timeouts
  - Unit tests for Seis, Consumer, and TvDatafeed classes
  - Mock fixtures for WebSocket and HTTP responses
  - Test coverage reporting (.coveragerc)

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
- **Dependencies updated**
  - pandas: 1.0.5 → >=1.3.0,<3.0.0
  - websocket-client: 0.57.0 → >=1.6.0,<2.0.0
  - requests: unversioned → >=2.28.0,<3.0.0
  - Added python-dotenv for environment variables
  - Added pyotp for future 2FA support

### Fixed
- Requirements.txt now has proper version constraints

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
