from logging import getLogger

from click import argument
from click import command
from rich.pretty import pprint

from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.decorators import require_platform_key
from ....utils.credentials import pass_azure_token
from ....utils.request import oauth_request
from ....utils.decorators import output_to_file

logger = getLogger("Babylon")


@command()
@timing_decorator
@pass_azure_token("csm_api")
@require_platform_key("api_url")
@argument("connector-id", type=QueryType())
@output_to_file
def get(azure_token: str, api_url: str, connector_id: str) -> CommandResponse:
    """Get a registered connector details."""
    response = oauth_request(f"{api_url}/connectors/{connector_id}", azure_token)
    if response is None:
        return CommandResponse.fail()
    connector = response.json()
    pprint(connector)
    return CommandResponse.success(connector)
