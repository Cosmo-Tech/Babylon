import logging
from typing import Optional

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import Context
from click import option
from click import argument

from ......utils.decorators import require_deployment_key
from ......utils.response import CommandResponse
from ......utils.request import oauth_request
from ......utils.typing import QueryType
from ......utils.interactive import confirm_deletion

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id", required=False)
@argument("dataset_id", type=QueryType())
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
def delete(ctx: Context,
           powerbi_workspace_id: str,
           dataset_id: str,
           workspace_id: Optional[str] = None,
           force_validation: bool = False) -> CommandResponse:
    """Delete a powerbi dataset in the current workspace"""
    workspace_id = workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    access_token = ctx.find_object(AccessToken).token
    if not force_validation and not confirm_deletion("dataset", dataset_id):
        return CommandResponse.fail()
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}"
    response = oauth_request(url, access_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Dataset id {dataset_id} successfully deleted.")
    return CommandResponse.success()
