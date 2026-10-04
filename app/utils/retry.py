import time
import functools
from typing import Callable, Any, Type, Tuple
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def retry(
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    tries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
) -> Callable:
    """
    Decorator for retrying a function with exponential backoff.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _tries, _delay = tries, delay
            while _tries > 1:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(
                        f"Function '{func.__name__}' failed with error: {e}. "
                        f"Retrying in {_delay:.1f}s... ({_tries - 1} retries left)"
                    )
                    time.sleep(_delay)
                    _tries -= 1
                    _delay *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator
