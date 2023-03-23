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
from ....utils.typing import QueryType

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@option("--filter", "filter", help="Filter response with a jmespath query")
@output_to_file
def get_all(api_url: str, azure_token: str, organization_id: str, filter: Optional[str] = None) -> CommandResponse:
    """Get all solutions from the organization"""
    logger.info(f"Getting all solutions from organization {organization_id}")
    response = oauth_request(f"{api_url}/organizations/{organization_id}/solutions", azure_token)
    if response is None:
        return CommandResponse.fail()
    solutions = response.json()
    if filter:
        solutions = jmespath.search(filter, solutions)
    return CommandResponse.success(solutions, verbose=True)
