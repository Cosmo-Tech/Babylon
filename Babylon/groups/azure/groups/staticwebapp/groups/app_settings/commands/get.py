import logging

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import Context
from click import argument
from rich.pretty import pretty_repr

from ........utils.request import oauth_request
from ........utils.decorators import require_platform_key
from ........utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_platform_key("azure_subscription", "azure_subscription")
@require_platform_key("resource_group_name", "resource_group_name")
@argument("webapp_name")
def get(ctx: Context, azure_subscription: str, resource_group_name: str, webapp_name: str) -> CommandResponse:
    """
    Get static webapp app settings for the given static web app
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/list-static-site-custom-domains
    """
    access_token = ctx.find_object(AccessToken).token
    response = oauth_request(
        f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
        f"providers/Microsoft.Web/staticSites/{webapp_name}/listAppSettings?api-version=2022-03-01",
        access_token,
        type="POST")
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success()
