# Contributing to TvDatafeed

Thank you for your interest in contributing to TvDatafeed! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Requesting Features](#requesting-features)

## Code of Conduct

This project follows a Code of Conduct. By participating, you are expected to uphold this code. Please be respectful and constructive in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/tvdatafeed.git
   cd tvdatafeed
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/rongardF/tvdatafeed.git
   ```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip
- virtualenv (recommended)

### Setup

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Install in development mode**:
   ```bash
   pip install -e .
   ```

4. **Set up environment variables** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your TradingView credentials
   ```

### Verify Setup

Run the tests to verify everything is working:
```bash
pytest
```

## Making Changes

### Branch Naming

Create a feature branch from `develop`:
```bash
git checkout develop
git pull upstream develop
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(datafeed): add support for 2FA authentication

Add two-factor authentication support for TradingView login.
Supports TOTP, SMS, and email-based 2FA.

Closes #123
```

```
fix(websocket): handle timeout errors gracefully

Add retry logic with exponential backoff for WebSocket timeouts.
Improves reliability when network is unstable.
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tvDatafeed --cov-report=html

# Run specific test file
pytest tests/unit/test_seis.py

# Run specific test
pytest tests/unit/test_seis.py::TestSeis::test_seis_creation
```

### Writing Tests

1. **Unit tests** go in `tests/unit/`
2. **Integration tests** go in `tests/integration/`
3. Use descriptive test names
4. Follow the AAA pattern (Arrange, Act, Assert)

Example:
```python
def test_seis_creation():
    """Test Seis object creation"""
    # Arrange
    symbol = 'BTCUSDT'
    exchange = 'BINANCE'
    interval = Interval.in_1_hour

    # Act
    seis = Seis(symbol, exchange, interval)

    # Assert
    assert seis.symbol == symbol
    assert seis.exchange == exchange
    assert seis.interval == interval
```

### Test Coverage

- Aim for **>80% coverage** for new code
- Test edge cases and error conditions
- Use mocks for external dependencies (WebSocket, HTTP requests)

## Code Style

### Python Style Guide

We follow **PEP 8** with some modifications:
- Maximum line length: **120 characters**
- Use **type hints** for all functions
- Write **docstrings** for all public functions

### Tools

**Black** (code formatter):
```bash
black tvDatafeed tests
```

**isort** (import sorter):
```bash
isort tvDatafeed tests
```

**pylint** (linter):
```bash
pylint tvDatafeed
```

**mypy** (type checker):
```bash
mypy tvDatafeed
```

### Docstring Format

Use **NumPy style** docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of the function

    Longer description if needed. Can span multiple lines.

    Parameters
    ----------
    param1 : str
        Description of param1
    param2 : int
        Description of param2

    Returns
    -------
    bool
        Description of return value

    Raises
    ------
    ValueError
        When param2 is negative

    Examples
    --------
    >>> function_name("test", 42)
    True
    """
    # Implementation
```

## Submitting Changes

### Before Submitting

1. **Run tests**: Ensure all tests pass
   ```bash
   pytest
   ```

2. **Check code style**:
   ```bash
   black tvDatafeed tests
   isort tvDatafeed tests
   pylint tvDatafeed
   ```

3. **Update documentation** if needed

4. **Add tests** for new features

5. **Update CHANGELOG.md** (if applicable)

### Pull Request Process

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub

3. **Fill in the PR template** with:
   - Description of changes
   - Related issue numbers
   - Testing done
   - Screenshots (if applicable)

4. **Wait for review**:
   - Address reviewer comments
   - Make requested changes
   - Push additional commits if needed

5. **Merge**: Once approved, a maintainer will merge your PR

### PR Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Commits are well-formed
- [ ] PR description is clear

## Reporting Bugs

### Before Reporting

1. **Check existing issues**: Search for similar bugs
2. **Try latest version**: Ensure bug exists in latest release
3. **Gather information**: Prepare code samples, error messages

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Initialize with '...'
2. Call method '...'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Code sample**
\```python
# Minimal code to reproduce
from tvDatafeed import TvDatafeed

tv = TvDatafeed()
# ...
\```

**Error message**
\```
Full error traceback
\```

**Environment:**
- OS: [e.g. Ubuntu 22.04]
- Python version: [e.g. 3.10.5]
- TvDatafeed version: [e.g. 2.1.0]

**Additional context**
Any other relevant information.
```

## Requesting Features

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Clear description of the problem.

**Describe the solution you'd like**
Clear description of what you want to happen.

**Describe alternatives you've considered**
Other solutions you've thought about.

**Additional context**
Mockups, examples, or any other context.

**Would you be willing to implement this feature?**
Yes/No/Maybe
```

## Development Workflow

### Typical Workflow

1. **Sync with upstream**:
   ```bash
   git checkout develop
   git pull upstream develop
   ```

2. **Create feature branch**:
   ```bash
   git checkout -b feature/my-feature
   ```

3. **Make changes**:
   - Write code
   - Write tests
   - Update docs

4. **Test**:
   ```bash
   pytest
   black tvDatafeed tests
   ```

5. **Commit**:
   ```bash
   git add .
   git commit -m "feat: add my feature"
   ```

6. **Push and create PR**:
   ```bash
   git push origin feature/my-feature
   ```

## Questions?

If you have questions:
1. Check the [README.md](README.md)
2. Look at [examples/](examples/)
3. Search [existing issues](https://github.com/rongardF/tvdatafeed/issues)
4. Create a new issue with the `question` label

## License

By contributing, you agree that your contributions will be licensed under the project's license.

---

Thank you for contributing to TvDatafeed! 🎉
