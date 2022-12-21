import logging
from uuid import uuid4

from azure.mgmt.kusto import KustoManagementClient
from azure.mgmt.kusto.models import DatabasePrincipalAssignment
from click import Choice
from click import Context
from click import argument
from click import command
from click import option
from click import pass_context

from ........utils.decorators import describe_dry_run
from ........utils.decorators import require_deployment_key
from ........utils.decorators import require_platform_key
from ........utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")
"""Command Tests
> babylon azure adx permission set "existing_principal_id" -r Viewer
Should ask for the missing principal type
> babylon azure adx permission set "existing_principal_id" -t App
Should ask for the missing principal role
> babylon azure adx permission set "existing_principal_id" -t App -r Viewer
Should ask for the missing principal role
> babylon azure adx permission set "unknown_principal_id" -t App -r Viewer
Should log a clean error message
"""


@command()
@pass_context
@require_platform_key("resource_group_name", "resource_group_name")
@require_platform_key("adx_cluster_name", "adx_cluster_name")
@require_deployment_key("adx_database_name", "adx_database_name")
@argument("principal_id", type=str)
@option("-r",
        "--role",
        type=Choice(["User", "Viewer", "Admin"], case_sensitive=False),
        required=True,
        help="Assignment Role to Add")
@option("-t",
        "--principal-type",
        type=Choice(["User", "Group", "App"], case_sensitive=False),
        required=True,
        help="Principal type of the given ID")
@describe_dry_run("Would add ROLE to PRINCIPAL_ID")
@timing_decorator
def set(ctx: Context, resource_group_name: str, adx_cluster_name: str, adx_database_name: str, principal_id: str,
        role: str, principal_type: str):
    """Set permission assignments applied to the given principal id"""
    kusto_mgmt: KustoManagementClient = ctx.obj
    parameters = DatabasePrincipalAssignment(principal_id=principal_id, principal_type=principal_type, role=role)
    principal_assignment_name = str(uuid4())
    logger.info("Creating assignment...")

    kusto_mgmt.database_principal_assignments.begin_create_or_update(resource_group_name, adx_cluster_name,
                                                                     adx_database_name, principal_assignment_name,
                                                                     parameters)
    logger.info(f"Successfully created a new {role} assignment to {principal_type} {principal_id}")
