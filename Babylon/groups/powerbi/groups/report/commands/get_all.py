import logging
from click import command
from click import pass_context
from click import Context
import requests

from ......utils.decorators import require_deployment_key

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id")
def get_all(ctx: Context, powerbi_workspace_id: str):
    """Get all info from powerbi reports"""
    access_token = ctx.obj.token
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{powerbi_workspace_id}/reports"
    response = requests.get(url=urls_reports, headers=header)
    logger.info(response.json()["value"])
