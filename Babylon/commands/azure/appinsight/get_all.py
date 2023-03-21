import logging
from rich.pretty import pretty_repr

from click import command

from ....utils.response import CommandResponse
from ....utils.request import oauth_request
from ....utils.decorators import require_platform_key
from ....utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token()
@require_platform_key("azure_subscription", "azure_subscription")
@require_platform_key("resource_group_name", "resource_group_name")
def get_all(azure_token: str, azure_subscription: str, resource_group_name: str) -> CommandResponse:
    """
    get all app insight data from a resource group
    https://learn.microsoft.com/en-us/rest/api/application-insights/components/list-by-resource-group
    """

    route = (f'https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/'
             f'providers/Microsoft.Insights/components?api-version=2015-05-01')
    response = oauth_request(route, azure_token, type="GET")
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)
