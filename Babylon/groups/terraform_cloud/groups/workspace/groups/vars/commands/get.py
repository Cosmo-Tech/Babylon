import json
import logging
import pathlib
import pprint
from typing import Optional

import click
from click import argument
from click import command
from click import option
from terrasnek.api import TFC

from ..list_all_vars import list_all_vars
from ........utils.decorators import timing_decorator
from ........utils.decorators import working_dir_requires_yaml_key
from ........utils.typing import QueryType

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
@argument("var_key", type=QueryType())
@timing_decorator
def get(api: TFC, workspace_id_wd: str, workspace_id: Optional[str], var_key: str, output_file: Optional[pathlib.Path]):
    """Get VAR_KEY variable in a workspace"""
    workspace_id = workspace_id or workspace_id_wd
    r = list(v for v in list_all_vars(api, workspace_id) if v['attributes']['key'] == var_key)

    if not r:
        logger.error(f"Var {var_key} is not set for workspace {workspace_id}")
        return

    logger.info(pprint.pformat(r[0]))

    if output_file:
        with open(output_file, "w") as _file:
            json.dump(r[0], _file, ensure_ascii=False)
