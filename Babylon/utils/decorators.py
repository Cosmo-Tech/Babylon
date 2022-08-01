import logging
import shutil
import time
from functools import wraps
from typing import Optional

import click
import cosmotech_api

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


def allow_dry_run(func):
    """
    Decorator adding dry_run parameter to the function call
    :param func: The function being decorated
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        env: Environment = click.get_current_context().find_object(Environment)
        kwargs["dry_run"] = env.dry_run
        func(*args, **kwargs)

    doc = wrapper.__doc__
    wrapper.__doc__ = doc + "\n\nAllows dry runs."
    return wrapper


def env_requires_yaml_key(yaml_path: str, yaml_key: str, arg_name: Optional[str] = None):
    """
    Decorator allowing to check if the environment has specific key in a yaml file.
    If the check is failed the command won't run, and following checks won't be done
    :param yaml_path: the path in the environment to the yaml file
    :param yaml_key: the required key
    :param arg_name: optional parameter that will send the value of the yaml key to the given arg of the function
    """

    def wrap_function(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            env: Environment = click.get_current_context().find_object(Environment)
            if env.requires_yaml_key(yaml_path=yaml_path, yaml_key=yaml_key):
                if arg_name is not None:
                    kwargs[arg_name] = env.get_yaml_key(yaml_path=yaml_path, yaml_key=yaml_key)
                func(*args, **kwargs)
            else:
                logger.error(f"Key {yaml_key} can not be found in {yaml_path}")
                logger.error(f"{click.get_current_context().command.name} won't run without it.")
                raise click.Abort()

        doc = wrapper.__doc__
        wrapper.__doc__ = (doc +
                           f"\n\nRequires key `{yaml_key}` in `{yaml_path}` in the environment.")
        return wrapper

    return wrap_function


def env_requires_file(file_path: str, arg_name: Optional[str] = None):
    """
    Decorator allowing to check if the environment has a specific file.
    If the check is failed the command won't run, and following checks won't be done
    :param file_path: the path in the environment to the required file
    :param arg_name: Optional parameter that if set will send the effective path of the required file to the given arg
    """

    def wrap_function(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            env: Environment = click.get_current_context().find_object(Environment)
            if env.requires_file(file_path=file_path):
                if arg_name is not None:
                    kwargs[arg_name] = env.get_file(file_path=file_path)
                func(*args, **kwargs)
            else:
                logger.error(f"Environment is missing {file_path}")
                logger.error(f"{click.get_current_context().command.name} won't run without it.")
                raise click.Abort()

        doc = wrapper.__doc__
        wrapper.__doc__ = (doc +
                           f"\n\nRequires the file `{file_path}` in the environment.")
        return wrapper

    return wrap_function


def requires_external_program(program_name: str):
    """
    Decorator allowing to check if a specific executable is available.
    If the check is failed the command won't run, and following checks won't be done
    :param program_name: the name of the required program
    """

    def wrap_function(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if shutil.which(program_name) is not None:
                func(*args, **kwargs)
            else:
                logger.error(f"{program_name} is not installed.")
                logger.error(f"{click.get_current_context().command.name} won't run without it.")
                raise click.Abort()

        doc = wrapper.__doc__
        wrapper.__doc__ = (doc +
                           f"\n\nRequires the program `{program_name}` to run.")
        return wrapper

    return wrap_function


pass_environment = click.make_pass_decorator(Environment)
pass_api_configuration = click.make_pass_decorator(cosmotech_api.Configuration)
