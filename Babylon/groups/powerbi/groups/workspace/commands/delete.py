import logging
from typing import Optional

import requests
from click import Context
from click import command
from click import option
from click import pass_context
from rich.pretty import pretty_repr

from ......utils.decorators import require_deployment_key
from ......utils.interactive import confirm_deletion
from ......utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_context
@option("-w", "--workspace", "override_workspace_id", required=False, type=QueryType())
@require_deployment_key("powerbi_workspace_id", required=False)
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
def delete(ctx: Context, powerbi_workspace_id: str, override_workspace_id: Optional[str], force_validation: bool):
    """Delete WORKSPACE_NAME from Power Bi APP"""
    access_token = ctx.parent.obj.token
    workspace_id = override_workspace_id or powerbi_workspace_id
    if not force_validation and not confirm_deletion("Power Bi Workspace", workspace_id):
        return
    url_delete = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}'
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    api_out = requests.delete(url=url_delete, headers=header)
    if api_out.status_code == 200:
        logger.info(f"{workspace_id} was successfully removed from power bi app")
    else:
        logger.error(f"Issues while removing {workspace_id}")
        logger.error(pretty_repr(api_out.__dict__))
