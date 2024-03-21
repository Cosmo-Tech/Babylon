import logging

from typing import Any
from click import command
from Babylon.utils.environment import Environment
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.commands.azure.adx.services.adx_permission_svc import AdxPermissionService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_kusto_client
@retrieve_state
def get_all(state: Any, kusto_client: KustoManagementClient):
    """
    Get all permission assignments in the database
    """
    service_state = state['services']
    service = AdxPermissionService(kusto_client=kusto_client, state=service_state)
    assignments = service.get_all()
    return CommandResponse.success({"assignments": assignments})
