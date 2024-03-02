import logging

from typing import Any
from click import command
from click import argument

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.decorators import timing_decorator
from Babylon.commands.azure.adx.services.permission import AdxPermissionService
from Babylon.utils.decorators import (
    retrieve_state,
    injectcontext,
)

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@pass_kusto_client
@argument("principal_id", type=str)
@retrieve_state
def get(state: Any, kusto_client: KustoManagementClient, principal_id: str) -> CommandResponse:
    """
    Get permission assignments applied to the given principal id
    """
    service_state = state['services']
    service = AdxPermissionService(kusto_client=kusto_client, state=service_state)
    entity_assignments = service.get(principal_id=principal_id)
    return CommandResponse.success({"assignments": entity_assignments})
