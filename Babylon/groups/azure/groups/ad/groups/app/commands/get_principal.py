import logging

from click import command
from click import argument
from rich.pretty import pretty_repr

from ........utils.request import oauth_request
from ........utils.response import CommandResponse
from ........utils.decorators import output_to_file
from ........utils.credentials import get_azure_token

logger = logging.getLogger("Babylon")


@command()
@argument("registration_id")
@output_to_file
def get_principal(registration_id: str) -> CommandResponse:
    """
    Get an app registration service principal in active directory
    https://learn.microsoft.com/en-us/graph/api/serviceprincipal-get
    """
    get_route = f"https://graph.microsoft.com/v1.0/applications/{registration_id}"
    access_token = get_azure_token("graph")
    get_response = oauth_request(get_route, access_token)
    if get_response is None:
        return CommandResponse.fail()
    app_id = get_response.json().get("appId")
    route = f"https://graph.microsoft.com/v1.0/servicePrincipals(appId='{app_id}')"
    response = oauth_request(route, access_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)
