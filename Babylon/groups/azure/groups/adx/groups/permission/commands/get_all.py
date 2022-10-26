import logging
from pprint import pformat

from azure.mgmt.kusto import KustoManagementClient
from click import Context
from click import command
from click import pass_context

from ........utils.decorators import require_deployment_key
from ........utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")
"""Command Tests
> babylon azure adx permission get-all
Should list all available assignments
"""


@command()
@pass_context
@require_platform_key("resource_group_name", "resource_group_name")
@require_platform_key("cluster_name", "cluster_name")
@require_deployment_key("database_name", "database_name")
def get_all(ctx: Context, resource_group_name: str, cluster_name: str, database_name: str):
    """Get all permission assignments in the database"""
    kusto_mgmt: KustoManagementClient = ctx.obj
    logger.info("Getting assignments...")
    assignments = kusto_mgmt.database_principal_assignments.list(resource_group_name, cluster_name, database_name)
    for ent in assignments:
        logger.info(f"{pformat(ent.__dict__)}")
