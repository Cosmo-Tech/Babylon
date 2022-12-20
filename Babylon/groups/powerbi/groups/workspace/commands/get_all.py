import json
import logging
from typing import Optional

import requests
from click import Context
from click import Path
from click import command
from click import option
from click import pass_context

from ......utils.logging import table_repr
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@option(
    "-o",
    "--output-file",
    "output_file",
    help="The path to the file where workspaces should be outputted (json-formatted)",
    type=Path(dir_okay=False),
)
def get_all(ctx: Context, output_file: Optional[str]) -> CommandResponse:
    """Get all workspace information for the given account"""
    access_token = ctx.parent.obj.token
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    response = requests.get(url=url_groups, headers=header)
    if response.status_code != 200:
        logger.error(f"Request failed: {response.text}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    groups = response.json()['value']
    if not output_file:
        logger.info("\n".join(table_repr(groups)))
        return CommandResponse(data=groups)
    with open(output_file, "w") as _f:
        json.dump(groups, _f)
    logger.info(f"Full content was dumped on {output_file}")
    return CommandResponse(data=groups)
