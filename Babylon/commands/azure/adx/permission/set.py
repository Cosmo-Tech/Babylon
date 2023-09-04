import logging

from typing import Any
from uuid import uuid4
from azure.mgmt.kusto import KustoManagementClient
from azure.mgmt.kusto.models import DatabasePrincipalAssignment
from click import Choice
from click import argument
from click import command
from click import option
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@timing_decorator
@pass_kusto_client
@option("--role",
        type=Choice(["User", "Viewer", "Admin"], case_sensitive=False),
        required=True,
        help="Assignment Role to Add")
@option("--principal-type",
        type=Choice(["User", "Group", "App"], case_sensitive=False),
        required=True,
        help="Principal type of the given ID")
@argument("principal_id", type=QueryType(), required=True)
@inject_context_with_resource({'azure': ['resource_group_name'], 'adx': ['cluster_name', 'database_name']})
def set(context: Any, kusto_client: KustoManagementClient, principal_id: str, role: str,
        principal_type: str) -> CommandResponse:
    """
    Set permission assignments applied to the given principal id
    """
    resource_group_name = context['azure_resource_group_name']
    adx_cluster_name = context['adx_cluster_name']
    database_name = context['adx_database_name']
    parameters = DatabasePrincipalAssignment(principal_id=principal_id, principal_type=principal_type, role=role)
    principal_assignment_name = str(uuid4())
    logger.info("Creating assignment...")
    poller = kusto_client.database_principal_assignments.begin_create_or_update(resource_group_name, adx_cluster_name,
                                                                                database_name,
                                                                                principal_assignment_name, parameters)
    if poller.done():
        logger.info("Successfully created")
    return CommandResponse.success()
