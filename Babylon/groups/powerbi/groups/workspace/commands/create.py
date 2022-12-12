import json
import logging
import pathlib
from typing import Optional

import requests
from click import Context
from click import Path
from click import command
from click import argument
from click import option
from click import pass_context

from ......utils.logging import table_repr
from ......utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_context
@option(
    "-o",
    "--output-file",
    "output_file",
    help="The path to the file where Solutions should be outputted (json-formatted)",
    type=Path(dir_okay=False, path_type=pathlib.Path),
)
@argument("workspace_name", type=QueryType())
def create(ctx: Context, workspace_name: str, output_file: Optional[Path]):
    """Create workspace named WORKSPACE_NAME into Power Bi App"""
    access_token = ctx.parent.obj.token
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups?$workspaceV2=True'
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    api_out = requests.post(url=url_groups, json={"name": workspace_name}, headers=header)
    groups = api_out.json()
    logger.info("\n".join(table_repr([
        groups,
    ])))
    if output_file:
        with open(output_file, "w") as _f:
            json.dump(groups, _f)
        logger.info(f"Full content was dumped on {output_file}")
