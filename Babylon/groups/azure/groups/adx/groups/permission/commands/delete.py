import logging

from azure.mgmt.kusto import KustoManagementClient
from click import Context
from click import argument
from click import command
from click import option
from click import pass_context

from ........utils.decorators import describe_dry_run
from ........utils.decorators import require_deployment_key
from ........utils.decorators import require_platform_key
from ........utils.interactive import confirm_deletion

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_platform_key("resource_group_name")
@require_platform_key("cluster_name")
@require_deployment_key("database_name")
@argument("principal_id", type=str)
@option("-f", "--force", "force_validation", is_flag=True, help="Don't ask for validation before delete")
@describe_dry_run("Would go through each role of given principal and delete them.")
def delete(ctx: Context,
           resource_group_name: str,
           cluster_name: str,
           database_name: str,
           principal_id: str,
           force_validation: bool = False):
    """Delete all permission assignments applied to the given principal id"""
    kusto_mgmt: KustoManagementClient = ctx.obj
    assignments = kusto_mgmt.database_principal_assignments.list(resource_group_name, cluster_name, database_name)
    entity_assignments = [assign for assign in assignments if assign.principal_id == principal_id]
    if not entity_assignments:
        logger.error(f"No assignment found for principal ID {principal_id}")
        return

    logger.info(f"Found {len(entity_assignments)} assignments for principal ID {principal_id}")
    for assign in entity_assignments:
        if not force_validation and not confirm_deletion("Permission", f"{assign.role}"):
            return

        logger.info(f"Deleting role {assign.role} to principal {assign.principal_type}:{assign.principal_id}")
        assign_name: str = str(assign.name).split("/")[-1]
        kusto_mgmt.database_principal_assignments.begin_delete(resource_group_name,
                                                               cluster_name,
                                                               database_name,
                                                               principal_assignment_name=assign_name)
