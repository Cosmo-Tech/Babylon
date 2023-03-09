import logging

from click import command
from click import argument
from click import option

from .....utils.request import oauth_request
from .....utils.decorators import require_platform_key
from .....utils.response import CommandResponse
from .....utils.interactive import confirm_deletion
from .....utils.credentials import pass_azure_token
from .....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("powerbi")
@require_platform_key("azure_subscription", "azure_subscription")
@require_platform_key("resource_group_name", "resource_group_name")
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
@argument("webapp_name", type=QueryType())
@argument("domain_name", type=QueryType())
def delete(azure_token: str,
           azure_subscription: str,
           resource_group_name: str,
           webapp_name: str,
           domain_name: str,
           force_validation: bool = False) -> CommandResponse:
    """
    Delete static webapp data from a resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/delete-static-site-custom-domain
    """
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
    logger.info(f"Successfully launched deletion of custom domain {domain_name} for static webapp {webapp_name}")
    return CommandResponse.success()
