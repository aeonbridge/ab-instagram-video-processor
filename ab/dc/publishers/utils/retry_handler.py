"""
Retry Handler Utility
Implements exponential backoff retry logic for API calls
"""

import time
import logging
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps

logger = logging.getLogger(__name__)


class RetryHandler:
    """Handles retries with exponential backoff"""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize retry handler

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Add random jitter to prevent thundering herd
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )

        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())  # 50-150% of calculated delay

        return delay

    def retry(
        self,
        func: Callable,
        *args,
        retry_on_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic

        Args:
            func: Function to execute
            *args: Positional arguments for function
            retry_on_exceptions: Tuple of exception types to retry on
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Retry successful after {attempt} attempts")
                return result

            except retry_on_exceptions as e:
                last_exception = e

                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"All {self.max_retries + 1} attempts failed. Last error: {str(e)}"
                    )

        raise last_exception

    def __call__(
        self,
        retry_on_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """
        Decorator for automatic retry

        Args:
            retry_on_exceptions: Tuple of exception types to retry on

        Example:
            @RetryHandler(max_retries=3)(retry_on_exceptions=(ConnectionError,))
            def upload_file():
                # ... upload logic
                pass
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.retry(
                    func,
                    *args,
                    retry_on_exceptions=retry_on_exceptions,
                    **kwargs
                )
            return wrapper
        return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for API calls
    Prevents cascading failures by stopping requests after threshold
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to count as failure
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception if circuit is open
        """
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "half-open"
                logger.info("Circuit breaker entering half-open state")
            else:
                raise Exception("Circuit breaker is OPEN - too many failures")

        try:
            result = func(*args, **kwargs)

            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker closed - service recovered")

            return result

        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(
                    f"Circuit breaker OPENED after {self.failure_count} failures"
                )

            raise e

    def reset(self):
        """Manually reset circuit breaker"""
        self.state = "closed"
        self.failure_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker manually reset")


# Convenience retry decorators for common scenarios

def retry_on_network_error(max_retries: int = 3):
    """Retry on network-related errors"""
    import requests
    handler = RetryHandler(max_retries=max_retries)
    return handler(
        retry_on_exceptions=(
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ChunkedEncodingError,
        )
    )


def retry_on_rate_limit(max_retries: int = 5, initial_delay: float = 5.0):
    """Retry on rate limit errors with longer delays"""
    handler = RetryHandler(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=300.0  # 5 minutes max
    )
    return handler(retry_on_exceptions=(Exception,))


def retry_on_server_error(max_retries: int = 3):
    """Retry on 5xx server errors"""
    import requests
    handler = RetryHandler(max_retries=max_retries)
    return handler(
        retry_on_exceptions=(
            requests.exceptions.HTTPError,
        )
    )
