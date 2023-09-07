from logging import getLogger
from typing import Optional

import jmespath
from click import argument
from click import command
from click import option

from ....utils.credentials import pass_azure_token
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.decorators import timing_decorator
from ....utils.request import oauth_request
from ....utils.response import CommandResponse
from ....utils.typing import QueryType

logger = getLogger("Babylon")


@command()
@timing_decorator
@pass_azure_token("csm_api")
@require_platform_key("api_url")
@argument("connector_id", type=QueryType())
@option("--filter", "filter", help="Filter response with a jmespath query")
@output_to_file
def get(azure_token: str, api_url: str, connector_id: str, filter: Optional[str] = None) -> CommandResponse:
    """Get a registered connector details."""
    response = oauth_request(f"{api_url}/connectors/{connector_id}", azure_token)
    if response is None:
        return CommandResponse.fail()
    connector = response.json()
    if filter:
        connector = jmespath.search(filter, connector)
    return CommandResponse.success(connector, verbose=True)
