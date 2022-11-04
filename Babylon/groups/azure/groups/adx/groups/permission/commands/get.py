import logging
from pprint import pformat

from azure.mgmt.kusto import KustoManagementClient
from click import Context
from click import argument
from click import command
from click import pass_context

from ........utils.decorators import require_deployment_key
from ........utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")
"""Command Tests
> babylon azure adx permission get "existing_principal_id"
Should return the principal assignments
> babylon azure adx permission get "unknown_principal_id"
Should log a clean error message
"""


@command()
@pass_context
@require_platform_key("resource_group_name")
@require_platform_key("cluster_name")
@require_deployment_key("database_name")
@argument("principal_id", type=str)
def get(ctx: Context, resource_group_name: str, cluster_name: str, database_name: str, principal_id: str):
    """Get permission assignments applied to the given principal id"""
    kusto_mgmt: KustoManagementClient = ctx.obj
    assignments = kusto_mgmt.database_principal_assignments.list(resource_group_name, cluster_name, database_name)
    entity_assignments = [assignment for assignment in assignments if assignment.principal_id == principal_id]
    if not entity_assignments:
        logger.info(f"No assignment found for principal ID {principal_id}")
        return
    logger.info(f"Found {len(entity_assignments)} assignments for principal ID {principal_id}")
    for ent in entity_assignments:
        logger.info(f"{pformat(ent.__dict__)}")
