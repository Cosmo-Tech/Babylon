from logging import getLogger
from typing import Optional

from click import command
from click import option
from rich.pretty import pprint

from ....utils.api import filter_api_response_item
from ....utils.decorators import timing_decorator
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
@option("-f", "--fields", "fields", help="Fields witch will be keep in response data, by default all")
@output_to_file
def get_all(
    azure_token: str,
    api_url: str,
    fields: Optional[str] = None,
) -> CommandResponse:
    """Get all connector details."""
    response = oauth_request(f"{api_url}/connectors", azure_token)
    if response is None:
        return CommandResponse.fail()
    retrieved_connector = response.json()
    if fields:
        retrieved_connector = filter_api_response_item(retrieved_connector, fields.replace(" ", "").split(","))
    pprint(retrieved_connector)
    return CommandResponse.success(retrieved_connector)
