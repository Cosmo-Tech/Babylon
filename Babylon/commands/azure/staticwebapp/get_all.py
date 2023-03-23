import logging
from typing import Optional

from click import command, option
import jmespath

from ....utils.request import oauth_request
from ....utils.decorators import require_platform_key
from ....utils.response import CommandResponse
from ....utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token()
@require_platform_key("azure_subscription", "azure_subscription")
@require_platform_key("resource_group_name", "resource_group_name")
@option("--filter", "filter", help="Filter response with a jmespath query")
def get_all(azure_token: str,
            azure_subscription: str,
            resource_group_name: str,
            filter: Optional[str] = None) -> CommandResponse:
    """
    Get all static webapps within the subscription
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/list
    """
    response = oauth_request(
        f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}"
        "/providers/Microsoft.Web/staticSites?api-version=2022-03-01", azure_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json().get("value")
    if filter:
        output_data = jmespath.search(filter, output_data)
    return CommandResponse.success(output_data, verbose=True)
