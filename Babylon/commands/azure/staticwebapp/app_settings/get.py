import logging

from typing import Any
from click import command
from click import argument
from Babylon.utils.request import oauth_request
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@pass_azure_token()
@argument("webapp_name", type=QueryType())
@inject_context_with_resource({'azure': ['resource_group_name', 'subscription_id']})
def get(context: Any, azure_token: str, webapp_name: str) -> CommandResponse:
    """
    Get static webapp app settings for the given static web app
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/list-static-site-app-settings
    """
    azure_subscription = context['azure_subscription_id']
    resource_group_name = context['azure_resource_group_name']
    response = oauth_request(
        f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
        f"providers/Microsoft.Web/staticSites/{webapp_name}/listAppSettings?api-version=2022-03-01",
        azure_token,
        type="POST")
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    return CommandResponse.success(output_data, verbose=True)
