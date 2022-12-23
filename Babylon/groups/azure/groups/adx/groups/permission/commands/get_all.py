import logging
from pprint import pformat

from azure.mgmt.kusto import KustoManagementClient
from click import Context
from click import command
from click import pass_context

from ........utils.decorators import require_deployment_key
from ........utils.decorators import require_platform_key
from ........utils.decorators import timing_decorator
from ........utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_platform_key("resource_group_name", "resource_group_name")
@require_platform_key("adx_cluster_name", "adx_cluster_name")
@require_deployment_key("adx_database_name", "adx_database_name")
@timing_decorator
def get_all(ctx: Context, resource_group_name: str, adx_cluster_name: str, adx_database_name: str):
    """Get all permission assignments in the database"""
    kusto_mgmt: KustoManagementClient = ctx.obj
    logger.info("Getting assignments...")
    assignments = kusto_mgmt.database_principal_assignments.list(resource_group_name, adx_cluster_name,
                                                                 adx_database_name)
    for ent in assignments:
        logger.info(f"{pformat(ent.__dict__)}")
    return CommandResponse(data={"assignments": assignments})
