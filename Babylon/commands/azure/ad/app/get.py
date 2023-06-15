import logging
import polling2

from click import command
from click import argument

from .....utils.request import oauth_request
from .....utils.response import CommandResponse
from .....utils.decorators import output_to_file
from .....utils.credentials import pass_azure_token
from .....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("graph")
@argument("object_id", type=QueryType())
@output_to_file
def get(azure_token: str, object_id: str) -> CommandResponse:
    """
    Get an app registration in active directory
    https://learn.microsoft.com/en-us/graph/api/application-get
    """
    route = f"https://graph.microsoft.com/v1.0/applications/{object_id}"
    # response = oauth_request(route, azure_token)

    response = polling2.poll(
        lambda: oauth_request(route, azure_token),
    check_success=is_correct_response,
    step=1,
    timeout=60)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    return CommandResponse.success(output_data, verbose=True)


def is_correct_response(response):
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    if "id" in output_data:
        return True