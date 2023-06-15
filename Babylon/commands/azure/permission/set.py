import logging
from typing import Optional
import uuid

from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.authorization.models import RoleAssignmentCreateParameters

from click import argument, option
from click import command

from ....utils.decorators import require_platform_key
from ....utils.decorators import require_deployment_key
from ....utils.response import CommandResponse
from ....utils.environment import Environment
from ....utils.typing import QueryType
from ....utils.clients import (
    get_azure_credentials,
)

logger = logging.getLogger("Babylon")


@command()
@require_deployment_key("organization_id")
@require_deployment_key("workspace_key")
@require_platform_key("csm_object_platform_id")
@option("-rt","--resource-type","resource_type", type=QueryType(), default="ServicePrincipal")
@option("-rn","--resource-name","resource_name", type=QueryType(), default="")
@option("-pt","--principal-type","principal_type", type=QueryType(), default="ServicePrincipal")
@option("-pi","--principal-id","principal_id", type=QueryType(), default="")
@option("-ri","--role-id","role_id", type=QueryType(), default="")
@option("--select-webapp","webapp_id", is_flag=True, type=QueryType(), default=False)
@require_platform_key("resource_group_name")
@require_platform_key("azure_subscription")
def set(
    organization_id: str,
    workspace_key: str,
    resource_group_name: str,
    azure_subscription: str,
    resource_type: str,
    resource_name: str,
    principal_type: str,
    webapp_id: bool,
    role_id: str,
    csm_object_platform_id: str,
    principal_id: Optional[str] = None,
) -> CommandResponse:
    """Assign a new role in resource given"""
    env = Environment()
    if not resource_name:
        resource_name = f"{organization_id.lower()}-{workspace_key.lower()}"
    
    if not principal_id:
        principal_id = csm_object_platform_id
    if webapp_id:
        principal_id = env.configuration.get_deploy_var("webapp_principal_id")
    scope = f"/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}/providers/{resource_type}/{resource_name}"

    authorization_client = AuthorizationManagementClient(
        credential=get_azure_credentials(),
        subscription_id=azure_subscription,
    )

    try:
        authorization_client.role_assignments.create(
            scope=scope,
            role_assignment_name=str(uuid.uuid4()),
            parameters=RoleAssignmentCreateParameters(
                
                role_definition_id=f"/subscriptions/{azure_subscription}/providers/Microsoft.Authorization/roleDefinitions/{role_id}",
                principal_id=principal_id,
                principal_type=principal_type
            )
        )
    except Exception as e:
        logger.error(f"Failed to assign a new role: {e}")

    return CommandResponse.success()
