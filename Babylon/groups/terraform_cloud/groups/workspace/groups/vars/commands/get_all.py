import json
import logging
import pathlib
import pprint
from typing import Optional

import click
from click import command
from click import option
from terrasnek.api import TFC

from ..list_all_vars import list_all_vars
from ........utils.decorators import timing_decorator
from ........utils.decorators import working_dir_requires_yaml_key
from ........utils.typing import QueryType
from ........utils.response import CommandResponse

logger = logging.getLogger("Babylon")

pass_tfc = click.make_pass_decorator(TFC)


@command()
@pass_tfc
@option(
    "-o",
    "--output",
    "output_file",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path),
    help="File to which content should be outputted (json-formatted)",
)
@option("-w", "--workspace", "workspace_id", help="Id of the workspace to use", type=QueryType())
@working_dir_requires_yaml_key("terraform_workspace.yaml", "workspace_id", "workspace_id_wd")
@timing_decorator
def get_all(api: TFC, workspace_id_wd: str, workspace_id: Optional[str],
            output_file: Optional[pathlib.Path]) -> CommandResponse:
    """Get all available variables in the workspace"""
    workspace_id = workspace_id or workspace_id_wd
    r = list_all_vars(api, workspace_id)
    if not r:
        logger.warning(f"No vars are set for workspace {workspace_id}")
    for ws_var in r:
        logger.info(pprint.pformat(ws_var))

    if output_file:
        with open(output_file, "w") as _file:
            json.dump(r, _file, ensure_ascii=False)
    return CommandResponse.success({"vars": r})
