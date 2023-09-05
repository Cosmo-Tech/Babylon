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
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@option("--filter", "filter", help="Filter response with a jmespath query")
@argument("solution_id", type=QueryType(), default="%deploy%solution_id")
@output_to_file
def get(api_url: str,
        azure_token: str,
        organization_id: str,
        solution_id: str,
        filter: Optional[str] = None) -> CommandResponse:
    """Get a solution from the organization"""
    response = oauth_request(f"{api_url}/organizations/{organization_id}/solutions/{solution_id}", azure_token)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    if filter:
        dataset = jmespath.search(filter, dataset)
    return CommandResponse.success(dataset, verbose=True)
