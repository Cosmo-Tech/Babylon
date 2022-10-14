import logging

from azure.mgmt.kusto import KustoManagementClient
from click import argument
from click import command
from click import confirm
from click import Context
from click import option
from click import pass_context

from ........utils.decorators import allow_dry_run
from ........utils.decorators import require_deployment_key
from ........utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")
"""Command Tests
> babylon azure adx permission delete "existing_principal_id"
Should ask confirmation, try y and no
> babylon azure adx permission delete "unknown_principal_id"
Should log a clean error message
"""


@command()
@pass_context
@require_platform_key("resource_group_name", "resource_group_name")
@require_platform_key("cluster_name", "cluster_name")
@require_deployment_key("database_name", "database_name")
@argument("principal_id")
@option("-f", "--force", is_flag=True, help="Don't ask for validation before delete")
@allow_dry_run
def delete(ctx: Context,
           resource_group_name: str,
           cluster_name: str,
           database_name: str,
           principal_id: str,
           dry_run: bool,
           force: bool = False):
    """Delete all permission assignments applied to the given principal id"""
    kusto_mgmt: KustoManagementClient = ctx.obj
    assignments = kusto_mgmt.database_principal_assignments.list(resource_group_name, cluster_name, database_name)
    entity_assignments = [assign for assign in assignments if assign.principal_id == principal_id]
    if not entity_assignments:
        logger.error(f"No assignment found for principal ID {principal_id}")
        return

    logger.info(f"Found {len(entity_assignments)} assignments for principal ID {principal_id}")
    for assign in entity_assignments:
        if not force and not confirm(
                f"Do you confirm deletion of {assign.role} permission for {assign.principal_name} ?"):
            logger.info(
                f"Aborting deletion of role {assign.role} to principal {assign.principal_type}:{assign.principal_id}")
            continue

        if dry_run:
            logger.info(f"Deleting role {assign.role} to principal {assign.principal_type}:{assign.principal_id}")
            continue

        assign_name: str = str(assign.name).split("/")[-1]
        kusto_mgmt.database_principal_assignments.begin_delete(resource_group_name,
                                                               cluster_name,
                                                               database_name,
                                                               principal_assignment_name=assign_name)
