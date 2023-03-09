import logging

from click import command
from click import argument
from rich.pretty import pretty_repr

from .....utils.request import oauth_request
from .....utils.response import CommandResponse
from .....utils.decorators import output_to_file
from .....utils.credentials import pass_azure_token
from .....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("graph")
@argument("registration_id", type=QueryType())
@output_to_file
def get_principal(azure_token: str, registration_id: str) -> CommandResponse:
    """
    Get an app registration service principal in active directory
    https://learn.microsoft.com/en-us/graph/api/serviceprincipal-get
    """
    get_route = f"https://graph.microsoft.com/v1.0/applications/{registration_id}"
    get_response = oauth_request(get_route, azure_token)
    if get_response is None:
        return CommandResponse.fail()
    app_id = get_response.json().get("appId")
    route = f"https://graph.microsoft.com/v1.0/servicePrincipals(appId='{app_id}')"
    response = oauth_request(route, azure_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)
