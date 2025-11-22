"""
Unit tests for utils module
"""
import time
import pytest
from unittest.mock import Mock, patch
from tvDatafeed.utils import (
    generate_session_id,
    generate_chart_session_id,
    retry_with_backoff,
    timeout_decorator,
    log_execution_time,
    mask_sensitive_data,
    format_timestamp,
    chunk_list,
    safe_divide,
    clamp,
    ContextTimer
)


@pytest.mark.unit
class TestSessionGeneration:
    """Test session ID generation functions"""

    def test_generate_session_id_default(self):
        """Test generating session ID with defaults"""
        session_id = generate_session_id()
        assert session_id.startswith("qs_")
        assert len(session_id) == 15  # "qs_" + 12 chars

    def test_generate_session_id_custom_prefix(self):
        """Test generating session ID with custom prefix"""
        session_id = generate_session_id(prefix="test", length=8)
        assert session_id.startswith("test_")
        assert len(session_id) == 13  # "test_" + 8 chars

    def test_generate_session_id_unique(self):
        """Test that generated IDs are unique"""
        ids = [generate_session_id() for _ in range(100)]
        assert len(ids) == len(set(ids))  # All unique

    def test_generate_chart_session_id(self):
        """Test generating chart session ID"""
        session_id = generate_chart_session_id()
        assert session_id.startswith("cs_")
        assert len(session_id) == 15


@pytest.mark.unit
class TestRetryWithBackoff:
    """Test retry with exponential backoff"""

    def test_retry_success_first_attempt(self):
        """Test successful execution on first attempt"""
        mock_func = Mock(return_value="success")

        result = retry_with_backoff(mock_func, max_retries=3)

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_success_after_failures(self):
        """Test successful execution after some failures"""
        mock_func = Mock(side_effect=[ValueError("error"), ValueError("error"), "success"])

        result = retry_with_backoff(
            mock_func,
            max_retries=3,
            base_delay=0.01,  # Very short delay for testing
            exceptions=(ValueError,)
        )

        assert result == "success"
        assert mock_func.call_count == 3

    def test_retry_all_attempts_fail(self):
        """Test when all retry attempts fail"""
        mock_func = Mock(side_effect=ValueError("persistent error"))

        with pytest.raises(ValueError, match="persistent error"):
            retry_with_backoff(
                mock_func,
                max_retries=2,
                base_delay=0.01,
                exceptions=(ValueError,)
            )

        assert mock_func.call_count == 3  # Initial + 2 retries

    def test_retry_callback_called(self):
        """Test that on_retry callback is called"""
        mock_func = Mock(side_effect=[ValueError("error"), "success"])
        callback = Mock()

        retry_with_backoff(
            mock_func,
            max_retries=2,
            base_delay=0.01,
            exceptions=(ValueError,),
            on_retry=callback
        )

        assert callback.call_count == 1
        # Verify callback was called with attempt number 1 and a ValueError exception
        args, kwargs = callback.call_args
        assert args[0] == 1
        assert isinstance(args[1], ValueError)

    def test_retry_wrong_exception_not_caught(self):
        """Test that wrong exception type is not caught"""
        mock_func = Mock(side_effect=TypeError("wrong type"))

        with pytest.raises(TypeError, match="wrong type"):
            retry_with_backoff(
                mock_func,
                max_retries=2,
                base_delay=0.01,
                exceptions=(ValueError,)
            )

        assert mock_func.call_count == 1  # No retries

    def test_retry_backoff_timing(self):
        """Test that backoff delays increase"""
        mock_func = Mock(side_effect=[ValueError(), ValueError(), "success"])

        start_time = time.time()
        retry_with_backoff(
            mock_func,
            max_retries=3,
            base_delay=0.1,
            exceptions=(ValueError,)
        )
        elapsed = time.time() - start_time

        # Should have delays of ~0.1s and ~0.2s (with jitter)
        # Total should be at least 0.2s but less than 1s
        assert 0.2 <= elapsed < 1.0


@pytest.mark.unit
class TestTimeoutDecorator:
    """Test timeout decorator"""

    def test_timeout_fast_function(self):
        """Test decorator with fast function"""
        @timeout_decorator(1.0)
        def fast_func():
            return "done"

        result = fast_func()
        assert result == "done"

    def test_timeout_slow_function(self):
        """Test decorator with slow function"""
        @timeout_decorator(0.1)
        def slow_func():
            time.sleep(0.2)
            return "done"

        with pytest.raises(TimeoutError, match="exceeded timeout"):
            slow_func()

    def test_timeout_with_args(self):
        """Test decorator with function arguments"""
        @timeout_decorator(1.0)
        def func_with_args(x, y):
            return x + y

        result = func_with_args(2, 3)
        assert result == 5


@pytest.mark.unit
class TestLogExecutionTime:
    """Test execution time logging decorator"""

    def test_log_execution_time_success(self, caplog):
        """Test logging successful execution time"""
        import logging
        caplog.set_level(logging.DEBUG)

        @log_execution_time
        def test_func():
            time.sleep(0.01)
            return "done"

        result = test_func()

        assert result == "done"
        # Check that debug log was created (timing message)
        assert any("completed in" in record.message for record in caplog.records)

    def test_log_execution_time_failure(self, caplog):
        """Test logging failed execution time"""
        @log_execution_time
        def failing_func():
            time.sleep(0.01)
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            failing_func()

        # Check that error log was created
        assert any("failed after" in record.message for record in caplog.records)


@pytest.mark.unit
class TestMaskSensitiveData:
    """Test sensitive data masking"""

    def test_mask_normal_string(self):
        """Test masking normal length string"""
        result = mask_sensitive_data("my_secret_token_12345")
        # Default visible_chars=4, so last 4 chars visible
        # String has 21 chars, so 17 asterisks + last 4 chars ("2345")
        assert result == "*****************2345"
        assert "secret" not in result
        assert result.endswith("2345")

    def test_mask_short_string(self):
        """Test masking very short string"""
        result = mask_sensitive_data("abc")
        assert result == "********"  # Fixed length mask

    def test_mask_custom_visible_chars(self):
        """Test masking with custom visible character count"""
        result = mask_sensitive_data("password123456", visible_chars=6)
        assert result == "********123456"

    def test_mask_custom_mask_char(self):
        """Test masking with custom mask character"""
        result = mask_sensitive_data("password123", visible_chars=3, mask_char='X')
        assert result == "XXXXXXXX123"

    def test_mask_empty_string(self):
        """Test masking empty string"""
        result = mask_sensitive_data("")
        assert result == "********"


@pytest.mark.unit
class TestFormatTimestamp:
    """Test timestamp formatting"""

    def test_format_timestamp_default(self):
        """Test formatting with default format"""
        timestamp = 1609459200.0  # 2021-01-01 00:00:00 UTC
        result = format_timestamp(timestamp)
        assert "2021-01-01" in result
        assert "00:00:00" in result

    def test_format_timestamp_custom(self):
        """Test formatting with custom format"""
        timestamp = 1609459200.0
        result = format_timestamp(timestamp, fmt="%Y-%m-%d")
        assert result == "2021-01-01"

    def test_format_timestamp_timezone(self):
        """Test that timezone is UTC"""
        timestamp = 0.0  # Unix epoch
        result = format_timestamp(timestamp)
        assert "1970-01-01" in result


@pytest.mark.unit
class TestChunkList:
    """Test list chunking"""

    def test_chunk_list_even(self):
        """Test chunking list with even division"""
        items = [1, 2, 3, 4, 5, 6]
        chunks = chunk_list(items, 2)
        assert chunks == [[1, 2], [3, 4], [5, 6]]

    def test_chunk_list_uneven(self):
        """Test chunking list with uneven division"""
        items = [1, 2, 3, 4, 5]
        chunks = chunk_list(items, 2)
        assert chunks == [[1, 2], [3, 4], [5]]

    def test_chunk_list_single_chunk(self):
        """Test chunking into single chunk"""
        items = [1, 2, 3]
        chunks = chunk_list(items, 10)
        assert chunks == [[1, 2, 3]]

    def test_chunk_list_empty(self):
        """Test chunking empty list"""
        chunks = chunk_list([], 2)
        assert chunks == []


@pytest.mark.unit
class TestSafeDivide:
    """Test safe division"""

    def test_safe_divide_normal(self):
        """Test normal division"""
        result = safe_divide(10, 2)
        assert result == 5.0

    def test_safe_divide_by_zero_default(self):
        """Test division by zero with default value"""
        result = safe_divide(10, 0)
        assert result == 0.0

    def test_safe_divide_by_zero_custom(self):
        """Test division by zero with custom default"""
        result = safe_divide(10, 0, default=float('inf'))
        assert result == float('inf')

    def test_safe_divide_float(self):
        """Test division with floats"""
        result = safe_divide(7.0, 2.0)
        assert result == 3.5


@pytest.mark.unit
class TestClamp:
    """Test value clamping"""

    def test_clamp_within_range(self):
        """Test clamping value within range"""
        result = clamp(5, 0, 10)
        assert result == 5

    def test_clamp_below_min(self):
        """Test clamping value below minimum"""
        result = clamp(-5, 0, 10)
        assert result == 0

    def test_clamp_above_max(self):
        """Test clamping value above maximum"""
        result = clamp(15, 0, 10)
        assert result == 10

    def test_clamp_at_boundaries(self):
        """Test clamping at exact boundaries"""
        assert clamp(0, 0, 10) == 0
        assert clamp(10, 0, 10) == 10

    def test_clamp_float(self):
        """Test clamping with floats"""
        result = clamp(5.5, 0.0, 10.0)
        assert result == 5.5


@pytest.mark.unit
class TestContextTimer:
    """Test context timer"""

    def test_context_timer_success(self, caplog):
        """Test timing successful operation"""
        import logging
        caplog.set_level(logging.DEBUG)

        with ContextTimer("Test operation"):
            time.sleep(0.01)

        # Check that timing was logged
        assert any("Test operation took" in record.message for record in caplog.records)

    def test_context_timer_failure(self, caplog):
        """Test timing failed operation"""
        try:
            with ContextTimer("Failing operation"):
                time.sleep(0.01)
                raise ValueError("test error")
        except ValueError:
            pass

        # Check that failure was logged
        assert any("Failing operation failed after" in record.message for record in caplog.records)

    def test_context_timer_elapsed(self):
        """Test getting elapsed time"""
        timer = ContextTimer("Test")

        with timer:
            time.sleep(0.05)

        assert 0.04 <= timer.elapsed <= 0.10

    def test_context_timer_custom_logger(self, caplog):
        """Test using custom logger instance"""
        import logging
        caplog.set_level(logging.DEBUG)
        custom_logger = logging.getLogger("custom")

        with ContextTimer("Custom logger test", logger_instance=custom_logger):
            pass

        # Check that custom logger was used
        assert any(record.name == "custom" for record in caplog.records)

    def test_context_timer_elapsed_before_exit(self):
        """Test elapsed is 0 before context exits"""
        timer = ContextTimer("Test")
        assert timer.elapsed == 0.0
