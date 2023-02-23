import logging

from click import command
from click import argument
from rich.pretty import pretty_repr

from ........utils.request import oauth_request
from ........utils.response import CommandResponse
from ........utils.decorators import output_to_file
from ........utils.decorators import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("graph")
@argument("registration_id")
@output_to_file
def get(azure_token: str, registration_id: str) -> CommandResponse:
    """
    Get an app registration in active directory
    https://learn.microsoft.com/en-us/graph/api/application-get
    """
    route = f"https://graph.microsoft.com/v1.0/applications/{registration_id}"
    response = oauth_request(route, azure_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)
