import logging

from typing import Any
from click import option
from click import command
from click import argument
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.decorators import describe_dry_run, wrapcontext
from Babylon.utils.decorators import retrieve_state, timing_decorator
from Babylon.commands.azure.adx.permission.service.api import AdxPermissionService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@pass_kusto_client
@describe_dry_run("Would go through each role of given principal and delete them.")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("principal_id", type=QueryType())
@retrieve_state
def delete(state: Any,
           kusto_client: KustoManagementClient,
           principal_id: str,
           force_validation: bool = False) -> CommandResponse:
    """
    Delete all permission assignments applied to the given principal id
    """
    service = AdxPermissionService(kusto_client=kusto_client, state=state)
    service.delete(
        force_validation=force_validation,
        principal_id=principal_id,
    )
    return CommandResponse.success()
