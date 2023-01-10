import logging
from rich.pretty import pretty_repr

from azure.core.credentials import AccessToken
from click import command
from click import Context, pass_context

from ......utils.response import CommandResponse
from ......utils.request import oauth_request
from ......utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_platform_key("azure_subscription", "azure_subscription")
@require_platform_key("resource_group_name", "resource_group_name")
def list(ctx: Context, azure_subscription: str, resource_group_name: str) -> CommandResponse:
    """
    list app insight data from a resource group
    https://learn.microsoft.com/en-us/rest/api/application-insights/components/list-by-resource-group
    """

    access_token = ctx.find_object(AccessToken).token
    route = (f'https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/'
             f'providers/Microsoft.Insights/components?api-version=2015-05-01')
    response = oauth_request(route, access_token, type="GET")
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)
