import logging

from pprint import pformat
from typing import Any
from azure.mgmt.kusto import KustoManagementClient
from click import argument
from click import command
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@timing_decorator
@pass_kusto_client
@argument("principal_id", type=QueryType())
@inject_context_with_resource({'azure': ['resource_group_name'], 'adx': ['cluster_name', 'database_name']})
def get(context: Any, kusto_client: KustoManagementClient, principal_id: str) -> CommandResponse:
    """
    Get permission assignments applied to the given principal id
    """
    resource_group_name = context['azure_resource_group_name']
    adx_cluster_name = context['adx_cluster_name']
    database_name = context['adx_database_name']
    assignments = kusto_client.database_principal_assignments.list(resource_group_name, adx_cluster_name, database_name)
    entity_assignments = [assignment for assignment in assignments if assignment.principal_id == principal_id]
    if not entity_assignments:
        logger.info(f"No assignment found for principal ID {principal_id}")
        return CommandResponse.fail()
    logger.info(f"Found {len(entity_assignments)} assignments for principal ID {principal_id}")
    for ent in entity_assignments:
        logger.info(f"{pformat(ent.__dict__)}")
    return CommandResponse.success({"assignments": entity_assignments})
