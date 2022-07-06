import logging
import time
from functools import wraps

import click

from .environment import Environment

logger = logging.getLogger("Babylon")


def timing_decorator(func):
    """
    Decorator adding timings before and after the run of a function
    :param func: The function being decorated
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"{func.__name__} : Starting")
        start_time = time.time()
        func(*args, **kwargs)
        logger.debug(f"{func.__name__} : Ending ({time.time() - start_time:.2f}s)")

    return wrapper


def env_requires_yaml_key(yaml_path: str, yaml_key: str):
    """
    Decorator allowing to check if the environment has specific key in a yaml file.
    If the check is failed the command won't run, and following checks won't be done
    :param yaml_path: the path in the environment to the yaml file
    :param yaml_key: the required key
    """
    def wrap_function(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            env: Environment = click.get_current_context().find_object(Environment)
            if env.requires_yaml_key(yaml_path=yaml_path, yaml_key=yaml_key):
                func(*args, **kwargs)
            else:
                logger.error(f"Key {yaml_key} can not be found in {yaml_path}")

        return wrapper

    return wrap_function


def env_requires_file(file_path: str):
    """
    Decorator allowing to check if the environment has a specific file.
    If the check is failed the command won't run, and following checks won't be done
    :param file_path: the path in the environment to the required file
    """
    def wrap_function(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            env: Environment = click.get_current_context().find_object(Environment)
            if env.requires_file(file_path=file_path):
                func(*args, **kwargs)
            else:
                logger.error(f"Environment is missing {file_path}")

        return wrapper

    return wrap_function


pass_environment = click.make_pass_decorator(Environment)
