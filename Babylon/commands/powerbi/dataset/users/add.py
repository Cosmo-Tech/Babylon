import logging

from typing import Any, Optional
from click import argument, command
from click import option
from Babylon.utils.checkers import check_email
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@pass_powerbi_token()
@option("--workspace", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("--email", "email", type=QueryType())
@argument("dataset_id", type=QueryType())
@inject_context_with_resource({"powerbi": ['workspace'], "azure": ['email']})
def add(context: Any,
        dataset_id: str,
        powerbi_token: str,
        workspace_id: str,
        email: str,
        filter: Optional[str] = None) -> CommandResponse:
    """
    Add user to dataset
    """
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    identifier = email or context['azure_email']
    check_email(identifier)
    gate_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/users"
    credential_details = {"identifier": identifier, "principalType": "User", "datasetUserAccessRight": "Read"}
    response = oauth_request(gate_url, powerbi_token, json=credential_details, type="POST")
    if response is None:
        return CommandResponse.fail()
    logger.info("Successfully added")
    return CommandResponse.success(response.text, verbose=True)
