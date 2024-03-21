import logging

from typing import Any, Optional
from click import command, option
from Babylon.commands.azure.appinsight.services.appinsight_api_svc import AzureAppInsightService
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import output_to_file

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_azure_token()
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any, azure_token: str, filter: Optional[str] = None) -> CommandResponse:
    """
    get all app insight data from a resource group
    https://learn.microsoft.com/en-us/rest/api/application-insights/components/list-by-resource-group
    """
    service_state = state['services']
    service = AzureAppInsightService(azure_token=azure_token, state=service_state)
    response = service.get_all(filter)
    return CommandResponse.success(response, verbose=True)
