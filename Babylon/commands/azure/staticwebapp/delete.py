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
@wrapcontext
@pass_azure_token()
@option("-D", "force_validation", is_flag=True, help="Delete on force mode")
@argument("name", type=QueryType())
@inject_context_with_resource({'azure': ['resource_group_name', 'subscription_id']})
def delete(context: Any, azure_token: str, name: str, force_validation: bool = False) -> CommandResponse:
    """
    Delete static webapp data from a resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/delete-static-site
    """
    azure_subscription = context['azure_subscription_id']
    resource_group_name = context['azure_resource_group_name']
    if not force_validation and not confirm_deletion("webapp", name):
        return CommandResponse.fail()
    logger.info(f"Deleting static webapp {name} from resource group {resource_group_name}")
    route = (f"https://management.azure.com/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/"
             f"providers/Microsoft.Web/staticSites/{name}?api-version=2022-03-01")
    response = oauth_request(route, azure_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully launched deletion of static webapp {name} from resource group {resource_group_name}")
    return CommandResponse.success()
