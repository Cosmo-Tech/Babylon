from logging import getLogger
from typing import Any, Optional
from click import command, option
import jmespath
from Babylon.commands.api.connectors.service.api import ApiConnectorService
from Babylon.utils.decorators import output_to_file, retrieve_state, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@output_to_file
@timing_decorator
@pass_azure_token("csm_api")
@option("--filter", "filter", type=str, help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any, azure_token: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all connectors details.
    Can be filtered with jmespath queries: https://jmespath.org/specification.html#grammar
    """
    service_state = state["services"]
    service = ApiConnectorService(azure_token=azure_token, state=service_state)
    response = service.get_all()
    if len(response) and filter:
        connectors = jmespath.search(filter, response)
    return CommandResponse.success(connectors, verbose=True)
