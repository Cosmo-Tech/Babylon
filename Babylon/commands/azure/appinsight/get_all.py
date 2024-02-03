import logging

from typing import Any, Optional
from click import command, option
from Babylon.commands.azure.appinsight.service.api import AzureAppInsightService
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import output_to_file

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@output_to_file
@pass_azure_token()
@option("--filter", "filter", help="Filter response with a jmespath query")
@inject_context_with_resource({"azure": ["resource_group_name", "subscription_id"]})
def get_all(
    context: Any, azure_token: str, filter: Optional[str] = None
) -> CommandResponse:
    """
    get all app insight data from a resource group
    https://learn.microsoft.com/en-us/rest/api/application-insights/components/list-by-resource-group
    """
    apiAppInsight = AzureAppInsightService(azure_token=azure_token, state=context)
    response = apiAppInsight.get_all()
    return CommandResponse.success(response, verbose=True)
