import logging
from functools import wraps
import time

logger = logging.getLogger("Babylon")


def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"{func.__name__} : Starting")
        start_time = time.time()
        func(*args, **kwargs)
        logger.debug(f"{func.__name__} : Ending ({time.time()-start_time:.2f}s)")

    return wrapper
