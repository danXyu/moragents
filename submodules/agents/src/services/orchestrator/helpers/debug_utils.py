"""Debug utilities for orchestration flow."""

import functools
import logging
import traceback
from typing import Any, Callable


logger = logging.getLogger(__name__)


def debug_errors(func: Callable) -> Callable:
    """Decorator to catch and log detailed error information."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the full stack trace
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Log function arguments for debugging
            logger.error(f"Args: {args}")
            logger.error(f"Kwargs: {kwargs}")
            
            # Re-raise the exception
            raise
    return wrapper


def debug_async_errors(func: Callable) -> Callable:
    """Decorator to catch and log detailed error information for async functions."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Log the full stack trace
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Log function arguments for debugging
            logger.error(f"Args: {args}")
            logger.error(f"Kwargs: {kwargs}")
            
            # Re-raise the exception
            raise
    return wrapper