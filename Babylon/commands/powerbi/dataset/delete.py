import logging
from typing import Any, Optional

from click import command
from click import option
from click import argument

from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.messages import SUCCESS_DELETED
from Babylon.utils.response import CommandResponse
from Babylon.utils.request import oauth_request
from Babylon.utils.typing import QueryType
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext
@pass_powerbi_token()
@option("--workspace", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("-D", "force_validation", is_flag=True, help="Delete on force mode")
@argument("dataset_id", type=QueryType())
@inject_context_with_resource({"powerbi": ['workspace']})
def delete(context: Any,
           powerbi_token: str,
           dataset_id: str,
           workspace_id: Optional[str] = None,
           force_validation: bool = False) -> CommandResponse:
    """
    Delete a powerbi dataset in the current workspace
    """
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    if not force_validation and not confirm_deletion("dataset", dataset_id):
        return CommandResponse.fail()

    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}"
    response = oauth_request(url, powerbi_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(SUCCESS_DELETED("dataset", dataset_id))
    return CommandResponse.success()
