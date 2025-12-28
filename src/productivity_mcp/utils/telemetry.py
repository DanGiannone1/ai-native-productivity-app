"""
Telemetry and logging decorators.
Adapted from enterprise_architecture template.
"""

import logging
import time
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


def with_telemetry(operation_name: str) -> Callable:
    """
    Decorator to add telemetry logging to functions.

    Logs:
    - Operation name
    - Duration (ms)
    - Success/failure status
    - Error messages

    Args:
        operation_name: Name of the operation for logging

    Example:
        @with_telemetry("create_task")
        def create_task(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            operation_id = f"{operation_name}:{int(start_time * 1000)}"

            logger.info(f"[{operation_id}] Starting {operation_name}")

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                logger.info(
                    f"[{operation_id}] ✓ {operation_name} completed successfully in {duration_ms:.2f}ms"
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                logger.error(
                    f"[{operation_id}] ✗ {operation_name} failed after {duration_ms:.2f}ms: {str(e)}"
                )

                raise

        return wrapper

    return decorator
