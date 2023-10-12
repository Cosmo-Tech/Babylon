import jmespath

from logging import getLogger
from typing import Any, Optional
from click import command, option
from Babylon.utils.typing import QueryType
from Babylon.utils.decorators import inject_context_with_resource, output_to_file, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@output_to_file
@timing_decorator
@pass_azure_token("csm_api")
@option("--filter", "filter", type=QueryType(), help="Filter response with a jmespath query")
@inject_context_with_resource({"api": ['url']})
def get_all(context: Any, azure_token: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all connectors details.
    Can be filtered with jmespath queries: https://jmespath.org/specification.html#grammar
    """
    response = oauth_request(f"{context['api_url']}/connectors", azure_token)
    if response is None:
        return CommandResponse.fail()
    connectors = response.json()
    if len(connectors) and filter:
        connectors = jmespath.search(filter, connectors)
    return CommandResponse.success(connectors, verbose=True)
