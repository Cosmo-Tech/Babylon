import logging
import jmespath
from typing import Any, Optional

from click import command, option

from Babylon.utils.request import oauth_request
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@pass_azure_token()
@option("--filter", "filter", help="Filter response with a jmespath query")
@inject_context_with_resource({'azure': ['resource_group_name', 'subscription_id']})
def get_all(context: Any, azure_token: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all static webapps within the subscription
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/list
    """
    azure_subscription = context['azure_subscription_id']
    resource_group_name = context['azure_resource_group_name']
    response = oauth_request(
        f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}"
        "/providers/Microsoft.Web/staticSites?api-version=2022-03-01", azure_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json().get("value")
    if filter:
        output_data = jmespath.search(filter, output_data)
    return CommandResponse.success(output_data, verbose=True)
