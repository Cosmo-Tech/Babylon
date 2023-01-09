import logging

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import Context
from click import argument
from click import option

from ......utils.request import oauth_request
from ......utils.decorators import require_platform_key
from ......utils.response import CommandResponse
from ......utils.interactive import confirm_deletion

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_platform_key("azure_subscription", "azure_subscription")
@require_platform_key("resource_group_name", "resource_group_name")
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
@argument("name")
def delete(ctx: Context,
           azure_subscription: str,
           resource_group_name: str,
           name: str,
           force_validation: bool = False) -> CommandResponse:
    """Delete static webapp data from a resource group"""
    if not force_validation and not confirm_deletion("webapp", name):
        logger.error("Plop")
        return CommandResponse.fail()
    logger.info(f"Deleting static webapp {name} from resource group {resource_group_name}")
    access_token = ctx.find_object(AccessToken).token
    response = oauth_request(
        f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
        f"providers/Microsoft.Web/staticSites/{name}?api-version=2022-03-01",
        access_token,
        type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully launched deletion of static webapp {name} from resource group {resource_group_name}")
    return CommandResponse.success()
