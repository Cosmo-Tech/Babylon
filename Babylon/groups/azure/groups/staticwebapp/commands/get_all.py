import logging

from azure.identity import DefaultAzureCredential
from click import command
from click import pass_context
from click import Context
from rich.pretty import pretty_repr

from ......utils.request import oauth_request
from ......utils.decorators import require_platform_key
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_platform_key("azure_subscription", "azure_subscription")
def get_all(ctx: Context, azure_subscription: str) -> CommandResponse:
    """Get all static webapps within the subscription"""
    credentials = ctx.find_object(DefaultAzureCredential)
    access_token = credentials.get_token("https://management.azure.com/.default").token
    response = oauth_request(
        f"https://management.azure.com/subscriptions/{azure_subscription}/providers/Microsoft.Web/staticSites?api-version=2022-03-01",
        access_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json().get("value")
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)
