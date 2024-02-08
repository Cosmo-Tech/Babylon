import datetime
import logging
import pathlib
import shutil
import time

from typing import Any
from functools import wraps
from typing import Callable
from Babylon.version import get_version
from click import get_current_context, option
from Babylon.utils.checkers import check_exists
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.config import config_files, get_settings_by_context

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


def inject_context(func):
    """
    Inject a dictionary of context to a command
    :param func: The function being decorated
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        context = dict()
        config_dir = env.configuration.config_dir
        for k in config_files:
            context[k] = get_settings_by_context(
                config_dir=config_dir,
                resource=k,
                context_id=env.context_id,
                environ_id=env.environ_id,
            )
        kwargs["context"] = context
        func(*args, **kwargs)
        return wrapper

    return wrapper


def inject_context_with_resource(scope, required: bool = True) -> Callable[..., Any]:
    """
    Inject a dictionary of context to a command from a specific resource
    """

    def wrap_function(func: Callable[..., Any]) -> Callable[..., Any]:

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            context = dict()
            _context = dict()
            config_dir = env.configuration.config_dir
            for i, k in scope.items():
                env.configuration.get_path(resource_id=i)
                context[i] = get_settings_by_context(
                    config_dir=config_dir,
                    resource=i,
                    context_id=env.context_id,
                    environ_id=env.environ_id,
                )
                for j in k:
                    _context.update({f"{i}_{j}": context[i][j]})
                    if required:
                        check_exists(i, j, _context)
            kwargs["context"] = _context
            return func(*args, **kwargs)

        return wrapper

    return wrap_function


def wrapcontext() -> Callable[..., Any]:

    def wrap_function(func: Callable[..., Any]) -> Callable[..., Any]:

        @option("-c", "--context", "context", required=True, help="Context Name")
        @option("-p", "--platform", "platform", required=True, help="Platform Name")
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            project = kwargs.pop("context", None)
            env.set_context(project)
            platform = kwargs.pop("platform", None)
            env.set_environ(platform)
            return func(*args, **kwargs)

        return wrapper

    return wrap_function


def retrieve_state(func) -> Callable[..., Any]:

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        init_state = dict()
        final_state = dict()
        final_state["services"] = dict()
        data_vault = env.get_state_from_vault_by_platform(env.environ_id)
        init_state["services"] = data_vault
        state_id = env.get_state_id()
        init_state["id"] = state_id
        state_cloud = env.get_state_from_cloud(init_state)
        env.store_state_in_local(state_cloud)
        for section, keys in state_cloud.get("services").items():
            final_state["services"][section] = dict()
            for key, _ in keys.items():
                final_state["services"][section].update({key: state_cloud["services"][section][key]})
                if data_vault[section][key]:
                    final_state["services"][section].update({key: data_vault[section][key]})
        final_state["id"] = init_state.get("id") or state_cloud.get("id")
        final_state["context"] = env.context_id
        final_state["platform"] = env.environ_id
        kwargs["state"] = final_state
        return func(*args, **kwargs)

    return wrapper
