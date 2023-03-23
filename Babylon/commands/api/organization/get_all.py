from logging import getLogger
from typing import Optional

from click import command
from click import option
import jmespath

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
@option("--filter", "filter", help="Filter response with a jmespath query")
@output_to_file
def get_all(api_url: str, azure_token: str, filter: Optional[str] = None) -> CommandResponse:
    """Get all organization details from the API."""
    response = oauth_request(f"{api_url}/organizations", azure_token)
    if response is None:
        return CommandResponse.fail()
    organizations = response.json()
    if filter:
        organizations = jmespath.search(filter, organizations)
    return CommandResponse.success(organizations, verbose=True)
