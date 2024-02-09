import logging

from typing import Any
from click import option
from click import Choice
from click import command
from click import argument
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.commands.azure.adx.permission.service.api import AdxPermissionService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@pass_kusto_client
@option("--role",
        type=Choice(["User", "Viewer", "Admin"], case_sensitive=False),
        required=True,
        help="Assignment Role to Add")
@option("--principal-type",
        type=Choice(["User", "Group", "App"], case_sensitive=False),
        required=True,
        help="Principal type of the given ID")
@argument("principal_id", type=QueryType(), required=True)
@retrieve_state
def set(state: Any, kusto_client: KustoManagementClient, principal_id: str, role: str,
        principal_type: str) -> CommandResponse:
    """
    Set permission assignments applied to the given principal id
    """
    service_state = state['services']
    service = AdxPermissionService(kusto_client=kusto_client, state=service_state)
    service.set(
        principal_id=principal_id,
        principal_type=principal_type,
        role=role,
    )
    return CommandResponse.success()
