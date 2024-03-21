import logging

from typing import Any
from click import command, argument
from Babylon.commands.azure.appinsight.services.appinsight_api_svc import AzureAppInsightService
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_azure_token()
@argument("name", type=str)
@retrieve_state
def get(state: Any, azure_token: str, name: str) -> CommandResponse:
    """
    Get app insight data from a name
    https://learn.microsoft.com/en-us/rest/api/application-insights/components/get
    """
    service_state = state['services']
    service = AzureAppInsightService(azure_token=azure_token, state=service_state)
    response = service.get(name=name)
    return CommandResponse.success(response, verbose=True)
