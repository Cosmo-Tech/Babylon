import logging

from click import command
from click import argument

from ....utils.request import oauth_request
from ....utils.decorators import require_platform_key
from ....utils.response import CommandResponse
from ....utils.credentials import pass_azure_token
from ....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token()
@require_platform_key("azure_subscription", "azure_subscription")
@require_platform_key("resource_group_name", "resource_group_name")
@argument("name", type=QueryType())
def get(azure_token: str, azure_subscription: str, resource_group_name: str, name: str) -> CommandResponse:
    """
    Get static webapp data from a resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/get-static-site
    """
    response = oauth_request(
        f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}"
        f"/providers/Microsoft.Web/staticSites/{name}?api-version=2022-03-01", azure_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    return CommandResponse.success(output_data, verbose=True)
