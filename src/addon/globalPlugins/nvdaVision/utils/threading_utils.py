"""Threading utilities for background operations."""

import threading
from typing import Callable, Any, Optional
from ..infrastructure.logger import logger


class TimeoutThread(threading.Thread):
    """Thread with timeout support for Windows."""

    def __init__(
        self,
        target: Callable,
        args: tuple = (),
        kwargs: dict = None,
        timeout: float = 15.0,
        name: str = "TimeoutThread"
    ):
        """Initialize timeout thread.

        Args:
            target: Function to run
            args: Positional arguments
            kwargs: Keyword arguments
            timeout: Timeout in seconds
            name: Thread name
        """
        super().__init__(name=name, daemon=True)
        self.target = target
        self.args = args
        self.kwargs = kwargs or {}
        self.timeout = timeout
        self.result: Optional[Any] = None
        self.exception: Optional[Exception] = None

    def run(self):
        """Run target function and capture result/exception."""
        try:
            self.result = self.target(*self.args, **self.kwargs)
        except Exception as e:
            self.exception = e
            logger.exception(f"Thread {self.name} raised exception")

    def get_result(self) -> Any:
        """Wait for result with timeout.

        Returns:
            Result from target function

        Raises:
            TimeoutError: If thread doesn't finish within timeout
            Exception: If target function raised an exception
        """
        self.join(timeout=self.timeout)

        if self.is_alive():
            # Thread still running - timeout
            raise TimeoutError(
                f"Function exceeded {self.timeout}s timeout"
            )

        if self.exception:
            raise self.exception

        return self.result


def run_with_timeout(
    func: Callable,
    *args,
    timeout: float = 15.0,
    **kwargs
) -> Any:
    """Run function with timeout (Windows-compatible).

    Args:
        func: Function to run
        *args: Positional arguments for func
        timeout: Timeout in seconds
        **kwargs: Keyword arguments for func

    Returns:
        Result from func

    Raises:
        TimeoutError: If func exceeds timeout

    Example:
        >>> result = run_with_timeout(slow_function, arg1, arg2, timeout=10.0)
    """
    thread = TimeoutThread(
        target=func,
        args=args,
        kwargs=kwargs,
        timeout=timeout
    )
    thread.start()
    return thread.get_result()


__all__ = [
    "TimeoutThread",
    "run_with_timeout",
]
