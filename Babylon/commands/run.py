import logging
import yaml
from typing import Dict, Any
import re
import click
from importlib import import_module
import jmespath

from ..utils.response import CommandResponse

logger = logging.getLogger("Babylon")


def execute_step(root: click.Context, step: Dict[str, Any]):
    logger.info(step.get("name"))
    commands = step.get("command", "").split(" ")
    to_import = "".join(
        ["Babylon", "".join([f".groups.{group}" for group in commands[:-1]]), f".commands.{commands[-1]}"])
    command_module = import_module(to_import, "Babylon")
    cmd = getattr(command_module, commands[-1])
    return root.invoke(cmd, **step.get("params", {}))


@click.command
@click.pass_context
@click.argument("script", type=click.Path(readable=True, dir_okay=False))
def run(ctx: click.Context, script: str):
    """Run a macro script"""
    with open(script, "r") as _f:
        macro = yaml.safe_load(_f)
    # Metadata
    logger.info(f"Running {macro.get('name')}")
    logger.info(macro.get("description"))
    # Executing steps
    root = ctx.find_root()
    forward_data = {}
    for step in macro.get("steps", []):

        # Insert values from forward in parameters
        for key, param in step.get("params", {}).items():
            needle = re.match(r"\$\w+\$", param)
            if not needle:
                continue
            fwd_k = needle.group().replace("$", "")
            # Replacing variable symbol by its actual value
            step["params"][key] = forward_data[fwd_k]

        response: CommandResponse = execute_step(root, step)

        # Forwarding response data to next commands
        for fwd_k, data_k in step.get("forward", {}).items():
            forward_data[fwd_k] = jmespath.search(data_k, response.data)

    logger.info(forward_data)
