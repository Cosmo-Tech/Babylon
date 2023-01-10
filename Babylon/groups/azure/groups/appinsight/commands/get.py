import logging
from rich.pretty import pretty_repr

from azure.core.credentials import AccessToken
from click import command, argument
from click import Context, pass_context

from ......utils.response import CommandResponse
from ......utils.request import oauth_request
from ......utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_platform_key("azure_subscription", "azure_subscription")
@require_platform_key("resource_group_name", "resource_group_name")
@argument("name")
def get(ctx: Context, azure_subscription: str, resource_group_name: str, name: str) -> CommandResponse:
    """
    Get app insight data from a name
    https://learn.microsoft.com/en-us/rest/api/application-insights/components/get
    """

    access_token = ctx.find_object(AccessToken).token
    route = (f'https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/'
             f'providers/Microsoft.Insights/components/{name}?api-version=2015-05-01')
    response = oauth_request(route, access_token, type="GET")
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)
