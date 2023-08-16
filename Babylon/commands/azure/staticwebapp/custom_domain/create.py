import logging
import pathlib

from typing import Any, Optional
from click import command
from click import argument
from click import Path
from click import option
from Babylon.utils.checkers import check_ascii
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@pass_azure_token()
@option("-f", "--file", "create_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@argument("webapp_name", type=QueryType())
@argument("domain_name", type=QueryType())
@inject_context_with_resource({'azure': ['resource_group_name', 'subscription_id']})
def create(context: Any,
           azure_token: str,
           webapp_name: str,
           domain_name: str,
           create_file: Optional[str] = None) -> CommandResponse:
    """
    Create a static webapp custom domain in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site-custom-domain
    """
    check_ascii(webapp_name)
    check_ascii(domain_name)
    azure_subscription = context['azure_subscription_id']
    resource_group_name = context['azure_resource_group_name']
    if not domain_name:
        return CommandResponse.fail()
    create_route = (
        f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
        f"providers/Microsoft.Web/staticSites/{webapp_name}/customDomains/{domain_name}?api-version=2022-03-01")
    details = '{"properties":{}}'
    if create_file:
        details = env.fill_template(create_file)
    response = oauth_request(create_route, azure_token, type="PUT", data=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info("Successfully launched")
    return CommandResponse.success(output_data, verbose=True)
