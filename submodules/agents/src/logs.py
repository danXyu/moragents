import logging
import sys


def setup_logging() -> logging.Logger:
    """
    Setup logging for the application.
    """
    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Setup file handler
    file_handler = logging.FileHandler("app.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove any existing handlers
    root_logger.handlers = []

    # Add our handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger
