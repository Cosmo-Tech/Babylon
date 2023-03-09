import logging
from pprint import pformat

from azure.mgmt.kusto import KustoManagementClient
from click import argument
from click import command

from ......utils.decorators import require_deployment_key
from ......utils.decorators import require_platform_key
from ......utils.decorators import timing_decorator
from ......utils.response import CommandResponse
from ......utils.clients import pass_kusto_client
from ......utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_kusto_client
@require_platform_key("resource_group_name", "resource_group_name")
@require_platform_key("adx_cluster_name", "adx_cluster_name")
@require_deployment_key("adx_database_name", "adx_database_name")
@argument("principal_id", type=QueryType())
@timing_decorator
def get(kusto_client: KustoManagementClient, resource_group_name: str, adx_cluster_name: str, adx_database_name: str,
        principal_id: str) -> CommandResponse:
    """Get permission assignments applied to the given principal id"""
    assignments = kusto_client.database_principal_assignments.list(resource_group_name, adx_cluster_name,
                                                                   adx_database_name)
    entity_assignments = [assignment for assignment in assignments if assignment.principal_id == principal_id]
    if not entity_assignments:
        logger.info(f"No assignment found for principal ID {principal_id}")
        return CommandResponse.fail()
    logger.info(f"Found {len(entity_assignments)} assignments for principal ID {principal_id}")
    for ent in entity_assignments:
        logger.info(f"{pformat(ent.__dict__)}")
    return CommandResponse.success({"assignments": entity_assignments})
