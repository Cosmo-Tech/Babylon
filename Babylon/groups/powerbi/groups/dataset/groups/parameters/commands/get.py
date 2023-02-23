import logging
from typing import Optional

from click import command
from click import argument
from click import option
from rich.pretty import pretty_repr

from ........utils.decorators import require_deployment_key
from ........utils.decorators import output_to_file
from ........utils.response import CommandResponse
from ........utils.typing import QueryType
from ........utils.request import oauth_request
from ........utils.decorators import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("powerbi")
@require_deployment_key("powerbi_workspace_id", required=False)
@argument("dataset_id", type=QueryType())
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
@output_to_file
def get(azure_token: str,
        powerbi_workspace_id: str,
        dataset_id: str,
        workspace_id: Optional[str] = None) -> CommandResponse:
    """Get parameters of a given dataset"""
    workspace_id = workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    update_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/parameters"
    response = oauth_request(update_url, azure_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json().get("value")
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)
