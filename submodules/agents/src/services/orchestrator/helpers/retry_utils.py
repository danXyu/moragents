"""Utilities for implementing retry logic with exponential backoff."""

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable, Type, Union

logger = logging.getLogger(__name__)


class RetryError(Exception):
    """Custom exception for retry exhaustion."""

    pass


def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0, jitter: bool = True) -> float:
    """Calculate exponential backoff delay with optional jitter."""
    delay = min(base_delay * (2**attempt), max_delay)
    if jitter:
        import random

        delay = delay * (0.5 + random.random() * 0.5)
    return delay


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Union[Type[Exception], tuple] = Exception,
    log_errors: bool = True,
):
    """Decorator for synchronous functions with retry logic and exponential backoff."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = exponential_backoff(attempt, base_delay, max_delay)
                        if log_errors:
                            logger.warning(
                                f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {str(e)}. "
                                f"Retrying in {delay:.1f} seconds..."
                            )
                        time.sleep(delay)
                    else:
                        if log_errors:
                            logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {str(e)}")

            raise RetryError(f"Failed after {max_attempts} attempts") from last_exception

        return wrapper

    return decorator


def async_retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Union[Type[Exception], tuple] = Exception,
    log_errors: bool = True,
):
    """Decorator for async functions with retry logic and exponential backoff."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = exponential_backoff(attempt, base_delay, max_delay)
                        if log_errors:
                            logger.warning(
                                f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {str(e)}. "
                                f"Retrying in {delay:.1f} seconds..."
                            )
                        await asyncio.sleep(delay)
                    else:
                        if log_errors:
                            logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {str(e)}")

            raise RetryError(f"Failed after {max_attempts} attempts") from last_exception

        return wrapper

    return decorator


class RetryManager:
    """Context manager for retry logic with exponential backoff."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exceptions: Union[Type[Exception], tuple] = Exception,
        log_errors: bool = True,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exceptions = exceptions
        self.log_errors = log_errors
        self.attempt = 0
        self.success = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.success = True
            return True

        if isinstance(exc_val, self.exceptions):
            self.attempt += 1
            if self.attempt < self.max_attempts:
                delay = exponential_backoff(self.attempt - 1, self.base_delay, self.max_delay)
                if self.log_errors:
                    logger.warning(
                        f"Attempt {self.attempt}/{self.max_attempts} failed: {str(exc_val)}. "
                        f"Will retry in {delay:.1f} seconds..."
                    )
                # Note: In a context manager, we can't actually sleep
                # This is mainly for tracking attempts
                return True
            else:
                if self.log_errors:
                    logger.error(f"All {self.max_attempts} attempts failed: {str(exc_val)}")
                return False

        return False

    def should_retry(self) -> bool:
        """Check if we should retry based on current attempt count."""
        return self.attempt < self.max_attempts and not self.success

    def sleep_before_retry(self):
        """Sleep for the appropriate backoff period."""
        if self.should_retry():
            delay = exponential_backoff(self.attempt - 1, self.base_delay, self.max_delay)
            time.sleep(delay)

    async def async_sleep_before_retry(self):
        """Async sleep for the appropriate backoff period."""
        if self.should_retry():
            delay = exponential_backoff(self.attempt - 1, self.base_delay, self.max_delay)
            await asyncio.sleep(delay)
