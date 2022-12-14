import json
import logging
import pathlib
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
@option("-w", "--workspace", "override_workspace_id", required=False, type=QueryType())
@require_deployment_key("powerbi_workspace_id", required=False)
def get_all(ctx: Context, powerbi_workspace_id: str, override_workspace_id: Optional[str], output_file: Optional[Path]):
    """List all exisiting users in the power bi workspace"""
    access_token = ctx.find_object(AccessToken).token
    workspace_id = override_workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return
    url_users = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users'
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    api_out = requests.get(url=url_users, headers=header)
    users = api_out.json()['value']
    logger.info("\n".join(table_repr(users)))
    if output_file:
        with open(output_file, "w") as _f:
            json.dump(users, _f)
        logger.info(f"Full content was dumped on {output_file}")
