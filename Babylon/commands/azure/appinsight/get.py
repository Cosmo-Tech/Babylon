import logging

from typing import Any
from click import command, argument
from Babylon.commands.azure.appinsight.service.api import AzureAppInsightService
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token()
@argument("name", type=QueryType())
@inject_context_with_resource({"azure": ["resource_group_name", "subscription_id"]})
def get(context: Any, azure_token: str, name: str) -> CommandResponse:
    """
    Get app insight data from a name
    https://learn.microsoft.com/en-us/rest/api/application-insights/components/get
    """
    apiAppInsight = AzureAppInsightService(azure_token=azure_token, state=context)
    response = apiAppInsight.get(name=name)
    return CommandResponse.success(response, verbose=True)
