import logging
from click import command
from click import pass_context
from click import Context
import requests

from ......utils.decorators import require_deployment_key
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id")
def get_all(ctx: Context, powerbi_workspace_id: str) -> CommandResponse:
    """Get a list of all powerbi datasets in the current workspace"""
    access_token = ctx.obj.token
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{powerbi_workspace_id}/datasets"
    try:
        response = requests.get(url=urls_reports, headers=header)
    except Exception as e:
        logger.error(f"Request failed {e}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    logger.info(response.json()["value"])
    return CommandResponse(data=response.json())
