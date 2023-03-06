import logging

from azure.mgmt.kusto import KustoManagementClient
from click import argument
from click import command
from click import option

from ........utils.decorators import describe_dry_run
from ........utils.decorators import require_deployment_key
from ........utils.decorators import require_platform_key
from ........utils.decorators import timing_decorator
from ........utils.interactive import confirm_deletion
from ........utils.response import CommandResponse
from ........utils.clients import pass_kusto_client

logger = logging.getLogger("Babylon")


@command()
@pass_kusto_client
@require_platform_key("resource_group_name", "resource_group_name")
@require_platform_key("adx_cluster_name", "adx_cluster_name")
@require_deployment_key("adx_database_name", "adx_database_name")
@argument("principal_id", type=str)
@option("-f", "--force", "force_validation", is_flag=True, help="Don't ask for validation before delete")
@describe_dry_run("Would go through each role of given principal and delete them.")
@timing_decorator
def delete(kusto_client: KustoManagementClient,
           resource_group_name: str,
           adx_cluster_name: str,
           adx_database_name: str,
           principal_id: str,
           force_validation: bool = False) -> CommandResponse:
    """Delete all permission assignments applied to the given principal id"""
    assignments = kusto_client.database_principal_assignments.list(resource_group_name, adx_cluster_name,
                                                                   adx_database_name)
    entity_assignments = [assign for assign in assignments if assign.principal_id == principal_id]
    if not entity_assignments:
        logger.error(f"No assignment found for principal ID {principal_id}")
        return CommandResponse.fail()

    logger.info(f"Found {len(entity_assignments)} assignments for principal ID {principal_id}")
    for assign in entity_assignments:

        if not force_validation and not confirm_deletion("permission", str(assign.role)):
            return CommandResponse.fail()

        logger.info(f"Deleting role {assign.role} to principal {assign.principal_type}:{assign.principal_id}")
        assign_name: str = str(assign.name).split("/")[-1]
        kusto_client.database_principal_assignments.begin_delete(resource_group_name,
                                                                 adx_cluster_name,
                                                                 adx_database_name,
                                                                 principal_assignment_name=assign_name)
    return CommandResponse.success()
