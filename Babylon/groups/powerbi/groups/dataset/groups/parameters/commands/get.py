import logging
import requests

from click import command
from click import argument
from click import pass_context
from click import Context

from ........utils.decorators import require_deployment_key
from ........utils.response import CommandResponse


logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id")
@argument("dataset_id")
def get(ctx: Context, powerbi_workspace_id: str, dataset_id: str) -> CommandResponse:
    """Get parameters of a given dataset"""
    access_token = ctx.obj.token
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    update_url = f"https://api.powerbi.com/v1.0/myorg/groups/{powerbi_workspace_id}/datasets/{dataset_id}/parameters"
    try:
        response = requests.get(url=update_url, headers=header)
    except Exception as e:
        logger.error(f"Request failed {e}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    logger.info(response.json())
    return CommandResponse(data=response.json())
