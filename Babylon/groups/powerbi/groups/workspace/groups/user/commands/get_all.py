import json
import logging
from typing import Optional

import requests
from azure.core.credentials import AccessToken
from click import Context
from click import Path
from click import command
from click import option
from click import pass_context

from ........utils.decorators import require_deployment_key
from ........utils.logging import table_repr
from ........utils.typing import QueryType
from ........utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@option(
    "-o",
    "--output-file",
    "output_file",
    help="The path to the file where Solutions should be outputted (json-formatted)",
    type=Path(dir_okay=False),
)
@option("-w", "--workspace", "override_workspace_id", type=QueryType())
@require_deployment_key("powerbi_workspace_id", required=False)
def get_all(ctx: Context,
            powerbi_workspace_id: str,
            override_workspace_id: Optional[str],
            output_file: Optional[str] = None) -> CommandResponse:
    """List all exisiting users in the power bi workspace"""
    access_token = ctx.find_object(AccessToken).token
    workspace_id = override_workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    url_users = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users'
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    try:
        api_out = requests.get(url=url_users, headers=header)
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    users = api_out.json()['value']
    if not output_file:
        logger.info("\n".join(table_repr(users)))
        return CommandResponse(data=users)
    with open(output_file, "w") as _f:
        json.dump(users, _f)
    logger.info(f"Full content was dumped on {output_file}")
    return CommandResponse(data=users)
