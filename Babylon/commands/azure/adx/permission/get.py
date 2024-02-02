import logging

from typing import Any
from click import argument
from click import command
from azure.mgmt.kusto import KustoManagementClient
from Babylon.commands.azure.adx.permission.service.api import AdxPermissionService
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@pass_kusto_client
@argument("principal_id", type=QueryType())
@inject_context_with_resource(
    {"azure": ["resource_group_name"], "adx": ["cluster_name", "database_name"]}
)
def get(
    context: Any, kusto_client: KustoManagementClient, principal_id: str
) -> CommandResponse:
    """
    Get permission assignments applied to the given principal id
    """
    apiAdxPermission = AdxPermissionService()
    entity_assignments = apiAdxPermission.get(
        context=context, principal_id=principal_id, kusto_client=kusto_client
    )
    return CommandResponse.success({"assignments": entity_assignments})
