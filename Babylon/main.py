#!/usr/bin/env python3
import logging
import sys
from pathlib import Path as pathlibPath
from re import sub

import click_log
from click import Path as clickPath
from click import echo, group, option
from rich.logging import RichHandler

from Babylon.commands import list_groups
from Babylon.utils.decorators import prepend_doc_with_ascii
from Babylon.utils.dry_run import display_dry_run
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import INTERACTIVE_ARG_VALUE, interactive_run
from Babylon.utils.telemetry import setup_telemetry
from Babylon.version import VERSION

trace = setup_telemetry()
tracer = trace.get_tracer(__name__)
logger = logging.getLogger()
logging.getLogger("azure").setLevel(logging.WARNING)
u_log = logging.getLogger("urllib3")
k_log = logging.getLogger("kubernetes")

# On bloque la propagation vers le haut (le root logger qui affiche dans la console)
u_log.propagate = False
k_log.propagate = False
env = Environment()


class CleanFormatter(logging.Formatter):
    """Formatter that removes [color] tags for file logs."""

    def format(self, record):
        original_msg = record.msg
        if isinstance(record.msg, str):
            record.msg = sub(r"\[\/?[a-zA-Z0-9 #]+\]", "", record.msg)

        result = super().format(record)
        record.msg = original_msg
        return result


def print_version(ctx, _, value):
    if not value or ctx.resilient_parsing:
        return
    echo(VERSION)
    ctx.exit()


def setup_logging(log_path: pathlibPath = pathlibPath.cwd()) -> None:
    import click  # noqa F401

    log_path.mkdir(parents=True, exist_ok=True)
    file_format = "%(asctime)s - %(levelname)s - %(name)s - %(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    file_formatter = CleanFormatter(fmt=file_format, datefmt=date_format)

    log_file_handler = logging.FileHandler(log_path / "babylon_info.log", encoding="utf-8")
    log_file_handler.setLevel(logging.INFO)
    log_file_handler.setFormatter(file_formatter)

    error_file_handler = logging.FileHandler(log_path / "babylon_error.log", encoding="utf-8")
    error_file_handler.setLevel(logging.WARNING)
    error_file_handler.setFormatter(file_formatter)
    logging.basicConfig(
        format="%(message)s",
        handlers=[
            log_file_handler,
            error_file_handler,
            RichHandler(
                show_time=False,
                rich_tracebacks=True,
                tracebacks_suppress=[click],
                omit_repeated_times=False,
                show_level=False,
                show_path=False,
                markup=True,
            ),
        ],
    )


@group(name="babylon", invoke_without_command=False)
@click_log.simple_verbosity_option(logger)
@option(
    "-n",
    "--dry-run",
    "dry_run",
    callback=display_dry_run,
    is_flag=True,
    expose_value=False,
    is_eager=True,
    help="Will run commands in dry-run mode.",
)
@option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Print version number and return.",
)
@option(
    "--log-path",
    "log_path",
    type=clickPath(file_okay=False, dir_okay=True, writable=True, path_type=pathlibPath),
    default=pathlibPath.cwd(),
    help="Path to the directory where log files will be stored. If not set, defaults to current working directory.",
)
@option(
    INTERACTIVE_ARG_VALUE,
    "interactive",
    is_flag=True,
    hidden=True,
    help="Start an interactive session after command run.",
)
@prepend_doc_with_ascii
def main(interactive, log_path):
    """
    CLI used for cloud interactions between CosmoTech and multiple cloud environment"""
    sys.tracebacklimit = 0
    setup_logging(pathlibPath(log_path))


main.result_callback()(interactive_run)

for _group in list_groups:
    main.add_command(_group)

if __name__ == "__main__":
    main()
