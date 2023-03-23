from logging import getLogger

from click import command
from rich.pretty import pprint

from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.credentials import pass_azure_token
from ....utils.request import oauth_request

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@output_to_file
def get_all(api_url: str, azure_token: str) -> CommandResponse:
    """Get all organization details from the API."""
    response = oauth_request(f"{api_url}/organizations", azure_token)
    if response is None:
        return CommandResponse.fail()
    organizations = response.json()
    pprint(organizations)
    return CommandResponse.success(organizations)
