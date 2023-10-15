import logging
import uuid

from typing import Any, Optional
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.authorization.models import RoleAssignmentCreateParameters
from click import Choice, option
from click import command
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType
from Babylon.utils.clients import (
    pass_iam_client, )

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_iam_client
@option("--resource-type", "resource_type", type=QueryType(), help="Ressource Type Id Azure")
@option("--resource-name", "resource_name", type=QueryType(), help="Ressource Name Azure")
@option("--principal-type",
        "principal_type",
        type=Choice(["User", "Group", "ServicePrincipal", "ForeignGroup", "Device"]),
        default="ServicePrincipal",
        help="Principal Type Azure")
@option("--principal-id", "principal_id", type=QueryType(), required=True, help="Principal Id Ressource")
@option("--role-id", "role_id", type=QueryType(), required=True, help="Role Id Ressource")
@inject_context_with_resource({
    'api': ['organization_id', 'workspace_key'],
    'azure': ['resource_group_name', 'subscription_id'],
    'platform': ['principal_id']
})
def set(
    context: Any,
    iam_client: AuthorizationManagementClient,
    resource_type: str,
    resource_name: str,
    principal_type: str,
    role_id: str,
    principal_id: Optional[str] = None,
) -> CommandResponse:
    """
    Assign a new role in resource given
    """
    organization_id = context['api_organization_id']
    workspace_key = context['api_workspace_key']
    azure_subscription = context['azure_subscription_id']
    resource_group_name = context['azure_resource_group_name']
    principal_id = principal_id or context['platform_principal_id']

    resource_name = resource_name or f"{organization_id.lower()}-{workspace_key.lower()}"
    prefix = f"/subscriptions/{azure_subscription}"
    scope = f"{prefix}/resourceGroups/{resource_group_name}/providers/{resource_type}/{resource_name}"
    role = f"{prefix}/providers/Microsoft.Authorization/roleDefinitions/{role_id}"
    try:
        iam_client.role_assignments.create(scope=scope,
                                           role_assignment_name=str(uuid.uuid4()),
                                           parameters=RoleAssignmentCreateParameters(role_definition_id=role,
                                                                                     principal_id=principal_id,
                                                                                     principal_type=principal_type))
    except Exception as e:
        logger.error(f"Failed to assign a new role: {e}")
    return CommandResponse.success()
