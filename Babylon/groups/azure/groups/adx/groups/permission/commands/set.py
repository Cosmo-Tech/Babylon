import logging

from azure.mgmt.kusto import KustoManagementClient
from azure.mgmt.kusto.models import DatabasePrincipalAssignment
from click import argument
from click import Choice
from click import command
from click import Context
from click import option
from click import pass_context
from uuid import uuid4

from ........utils.decorators import require_platform_key
from ........utils.decorators import require_deployment_key
from ........utils.decorators import allow_dry_run

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
@require_platform_key("cluster_name", "cluster_name")
@require_deployment_key("database_name", "database_name")
@argument("principal_id")
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
@allow_dry_run
def set(ctx: Context, resource_group_name: str, cluster_name: str, database_name: str, principal_id: str, role: str,
        principal_type: str, dry_run: bool):
    """Get permission assignments applied to the given principal id"""
    kusto_mgmt: KustoManagementClient = ctx.obj
    parameters = DatabasePrincipalAssignment(principal_id=principal_id, principal_type=principal_type, role=role)
    principal_assignment_name = str(uuid4())
    logger.info("Creating assignment...")

    if dry_run:
        logger.info(f"Adding role {role} to principal {principal_type}:{principal_id}")
        return

    kusto_mgmt.database_principal_assignments.begin_create_or_update(resource_group_name, cluster_name, database_name,
                                                                     principal_assignment_name, parameters)
    logger.info(f"Successfully created a new {role} assignment to {principal_type} {principal_id}")
