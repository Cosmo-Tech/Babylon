import logging

from typing import Any
from azure.mgmt.kusto import KustoManagementClient
from click import argument
from click import command
from click import option
from Babylon.utils.decorators import describe_dry_run, wrapcontext
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.interactive import confirm_deletion
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
@describe_dry_run("Would go through each role of given principal and delete them.")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("principal_id", type=QueryType())
@inject_context_with_resource({'azure': ['resource_group_name'], 'adx': ['cluster_name', 'database_name']})
def delete(context: Any,
           kusto_client: KustoManagementClient,
           principal_id: str,
           force_validation: bool = False) -> CommandResponse:
    """
    Delete all permission assignments applied to the given principal id
    """
    resource_group_name = context['azure_resource_group_name']
    adx_cluster_name = context['adx_cluster_name']
    database_name = context['adx_database_name']
    assignments = kusto_client.database_principal_assignments.list(resource_group_name, adx_cluster_name, database_name)
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
                                                                 database_name,
                                                                 principal_assignment_name=assign_name)
    return CommandResponse.success()
