import logging
from typing import Optional

from click import command, option
import jmespath

from ....utils.response import CommandResponse
from ....utils.request import oauth_request
from ....utils.decorators import require_platform_key
from ....utils.credentials import pass_azure_token
from ....utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token()
@require_platform_key("azure_subscription")
@require_platform_key("resource_group_name")
@option("--filter", "filter", help="Filter response with a jmespath query")
@output_to_file
def get_all(azure_token: str,
            azure_subscription: str,
            resource_group_name: str,
            filter: Optional[str] = None) -> CommandResponse:
    """
    get all app insight data from a resource group
    https://learn.microsoft.com/en-us/rest/api/application-insights/components/list-by-resource-group
    """

    route = (f'https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/'
             f'providers/Microsoft.Insights/components?api-version=2015-05-01')
    response = oauth_request(route, azure_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()["value"]
    if filter:
        output_data = jmespath.search(filter, output_data)
    return CommandResponse.success(output_data, verbose=True)
