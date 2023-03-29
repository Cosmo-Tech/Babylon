from logging import getLogger
from typing import Optional

from click import command
from click import option
import jmespath

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
@option("--filter", "filter", help="Filter response with a jmespath query")
@output_to_file
def get_all(
    azure_token: str,
    api_url: str,
    filter: Optional[str] = None,
) -> CommandResponse:
    """
    Get all connector details.
    Can be filtered with jmespath queries: https://jmespath.org/specification.html#grammar
    """
    response = oauth_request(f"{api_url}/connectors", azure_token)
    if response is None:
        return CommandResponse.fail()
    connectors = response.json()
    if filter:
        connectors = jmespath.search(filter, connectors)
    return CommandResponse.success(connectors, verbose=True)
