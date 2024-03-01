import logging

from typing import Any
from click import command, argument, option
from Babylon.commands.azure.appinsight.services.api import AzureAppInsightService
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_azure_token()
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("name", type=QueryType())
@retrieve_state
def delete(state: Any, azure_token: str, name: str, force_validation: str) -> CommandResponse:
    """
    Delete app insight data from a name
    https://learn.microsoft.com/en-us/rest/api/application-insights/components/delete
    """
    service_state = state['services']
    service = AzureAppInsightService(azure_token=azure_token, state=service_state)
    service.delete(
        name=name,
        force_validation=force_validation,
    )
    return CommandResponse.success()
