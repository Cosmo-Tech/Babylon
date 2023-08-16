import logging

from typing import Any
from click import command
from click import argument
from click import option
from Babylon.utils.request import oauth_request
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token()
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("webapp_name", type=QueryType())
@argument("domain_name", type=QueryType())
@inject_context_with_resource({'azure': ['resource_group_name', 'subscription_id']})
def delete(context: Any,
           azure_token: str,
           webapp_name: str,
           domain_name: str,
           force_validation: bool = False) -> CommandResponse:
    """
    Delete static webapp data from a resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/delete-static-site-custom-domain
    """
    azure_subscription = context['azure_subscription_id']
    resource_group_name = context['azure_resource_group_name']
    if not force_validation and not confirm_deletion("domain", domain_name):
        return CommandResponse.fail()
    logger.info(f"Deleting custom domain {domain_name} for static webapp {webapp_name}")
    response = oauth_request(
        f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
        f"providers/Microsoft.Web/staticSites/{webapp_name}/customDomains/{domain_name}?api-version=2022-03-01",
        azure_token,
        type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info("Successfully launched")
    return CommandResponse.success()
