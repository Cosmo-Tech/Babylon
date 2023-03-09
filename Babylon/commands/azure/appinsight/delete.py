import logging

from click import command, argument

from ....utils.response import CommandResponse
from ....utils.request import oauth_request
from ....utils.decorators import require_platform_key
from ....utils.credentials import pass_azure_token
from ....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token()
@require_platform_key("azure_subscription", "azure_subscription")
@require_platform_key("resource_group_name", "resource_group_name")
@argument("name", type=QueryType())
def delete(azure_token: str, azure_subscription: str, resource_group_name: str, name: str) -> CommandResponse:
    """
    Delete app insight data from a name
    https://learn.microsoft.com/en-us/rest/api/application-insights/components/delete
    """

    route = (f'https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/'
             f'providers/Microsoft.Insights/components/{name}?api-version=2015-05-01')
    response = oauth_request(route, azure_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    if response.status_code == 204:
        logger.warn(f"App Insight {name} doesn't exist")
        return CommandResponse.fail()
    logger.info(f'App Insight {name} has been successfully deleted.')
    return CommandResponse.success()
