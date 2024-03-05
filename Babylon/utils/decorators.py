import datetime
import logging
import pathlib
import shutil
import time

from typing import Any
from functools import wraps
from typing import Callable
from Babylon.utils.checkers import check_special_char
from Babylon.version import get_version
from click import get_current_context, option
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


def prepend_doc_with_ascii(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator used to add a babylon ascii art in the documentation of a function
    :param func: The function being decorated
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    babylon_ascii = (
        "\b",
        r" ____              __                 ___  ",
        r"/\  _`\           /\ \               /\_ \  ",
        r"\ \ \L\ \     __  \ \ \____   __  __ \//\ \      ___     ___  ",
        r" \ \  _ <'  /'__`\ \ \ '__`\ /\ \/\ \  \ \ \    / __`\ /' _ `\  ",
        r"  \ \ \L\ \/\ \L\.\_\ \ \L\ \\ \ \_\ \  \_\ \_ /\ \L\ \/\ \/\ \  ",
        r"   \ \____/\ \__/.\_\\ \_,__/ \/`____ \ /\____\\ \____/\ \_\ \_\  ",
        r"    \/___/  \/__/\/_/ \/___/   `/___/> \\/____/ \/___/  \/_/\/_/  ",
        r"                                  /\___/  ",
        r"                                  \/__/  ",
        f"                                                           v{get_version()}\n",
        "",
    )
    doc = wrapper.__doc__ or ""
    wrapper.__doc__ = "\n".join(babylon_ascii) + doc
    return wrapper


def output_to_file(func: Callable[..., Any]) -> Callable[..., Any]:
    """Add output to file option to a command"""

    @option(
        "-o",
        "--output",
        "output_file",
        help="File to which content should be outputted",
    )
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        output_file = kwargs.pop("output_file", None)
        if output_file:
            path_file = pathlib.Path(output_file)
            ext_file = path_file.suffix
        response: CommandResponse = func(*args, **kwargs)
        if output_file:
            output_file = pathlib.Path(output_file)
            if "json" in ext_file:
                response.dump_json(output_file)
            else:
                response.dump_yaml(output_file)
        return response

    return wrapper


def timing_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator adding timings before and after the run of a function
    :param func: The function being decorated
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.info(f"{func.__name__} - Starting")
        start_time = time.time()
        resp: CommandResponse = func(*args, **kwargs)
        end_time = time.time()
        lapsed = end_time - start_time
        logger.info(f"{func.__name__} - Total elapsed time: {datetime.timedelta(seconds = lapsed)}")
        return resp

    return wrapper


def describe_dry_run(description: str):
    """
    Add a dry run description for the decorated call
    :param description: description to de displayed during dry runs (accepts markdown content)
    """

    def wrap_function(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.dry_run = description
        return wrapper

    return wrap_function


def requires_external_program(program_name: str) -> Callable[..., Any]:
    """
    Decorator allowing to check if a specific executable is available.
    If the check is failed the command won't run, and following checks won't be done
    :param program_name: the name of the required program
    """

    def wrap_function(func: Callable[..., Any]) -> Callable[..., Any]:

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            if shutil.which(program_name):
                return func(*args, **kwargs)

            logger.error(f"{program_name} is not installed")
            logger.error(f"{get_current_context().command.name} won't run without it")
            raise FileNotFoundError(f"{program_name} is not installed")

        doc = wrapper.__doc__ or ""
        wrapper.__doc__ = "\n\n".join([doc, f"Requires the program `{program_name}` to run"])
        return wrapper

    return wrap_function


<<<<<<< HEAD
def injectcontext() -> Callable[..., Any]:

    def wrap_function(func: Callable[..., Any]) -> Callable[..., Any]:

        @option(
            "-c",
            "--context",
            "context",
            help="Context Name without any special character",
        )
        @option(
            "-p",
            "--platform",
            "platform",
            help="Platform Id without any special character",
        )
        @option(
            "-s",
            "--state-id",
            "state_id",
            help="State Id",
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            context = kwargs.pop("context", None)
            if context and check_special_char(string=context):
                env.set_context(context)
            platform = kwargs.pop("platform", None)
            if platform and check_special_char(string=platform):
                env.set_environ(platform)
            state_id = kwargs.pop("state_id", None)
            if state_id and check_special_char(string=state_id):
                env.set_state_id(state_id)
            env.get_namespace_from_local(context=context, platform=platform, state_id=state_id)
            return func(*args, **kwargs)

        return wrapper

    return wrap_function


def retrieve_state(func) -> Callable[..., Any]:

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        state = env.retrieve_state_func(state_id=env.state_id)
        kwargs["state"] = state
        return func(*args, **kwargs)

    return wrapper


def wrapcontext() -> Callable[..., Any]:

    def wrap_function(func: Callable[..., Any]) -> Callable[..., Any]:

        @option("-c", "--context", "context", required=True, help="Context Name")
        @option("-p", "--platform", "platform", required=True, help="Platform Name")
        @option("-s", "--state-id", "state_id", required=True, help="State Id")
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            context = kwargs.pop("context", None)
            if context and check_special_char(string=context):
                env.set_context(context)
            platform = kwargs.pop("platform", None)
            if platform and check_special_char(string=platform):
                env.set_environ(platform)
            state_id = kwargs.pop("state_id", None)
            if state_id and check_special_char(string=state_id):
                env.set_state_id(state_id)
            return func(*args, **kwargs)

        return wrapper

    return wrap_function


=======
>>>>>>> 53b0a6f8 (add injectcontext)
def injectcontext() -> Callable[..., Any]:

    def wrap_function(func: Callable[..., Any]) -> Callable[..., Any]:

        @option(
            "-c",
            "--context",
            "context",
            help="Context Name without any special character",
        )
        @option(
            "-p",
            "--platform",
            "platform",
            help="Platform Id without any special character",
        )
        @option(
            "-s",
            "--state-id",
            "state_id",
            help="State Id",
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            context = kwargs.pop("context", None)
            if context and check_special_char(string=context):
                env.set_context(context)
            platform = kwargs.pop("platform", None)
            if platform and check_special_char(string=platform):
                env.set_environ(platform)
            state_id = kwargs.pop("state_id", None)
            if state_id and check_special_char(string=state_id):
                env.set_state_id(state_id)
            env.get_namespace_from_local(context=context, platform=platform, state_id=state_id)
            return func(*args, **kwargs)

        return wrapper

    return wrap_function


def retrieve_state(func) -> Callable[..., Any]:

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        state = env.retrieve_state_func(state_id=env.state_id)
        kwargs["state"] = state
        return func(*args, **kwargs)

    return wrapper


def wrapcontext() -> Callable[..., Any]:

    def wrap_function(func: Callable[..., Any]) -> Callable[..., Any]:

        @option("-c", "--context", "context", required=True, help="Context Name")
        @option("-p", "--platform", "platform", required=True, help="Platform Name")
        @option("-s", "--state-id", "state_id", required=True, help="State Id")
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            context = kwargs.pop("context", None)
            if context and check_special_char(string=context):
                env.set_context(context)
            platform = kwargs.pop("platform", None)
            if platform and check_special_char(string=platform):
                env.set_environ(platform)
            state_id = kwargs.pop("state_id", None)
            if state_id and check_special_char(string=state_id):
                env.set_state_id(state_id)
            return func(*args, **kwargs)
        return wrapper

    return wrap_function
