import logging
import uuid

from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.authorization.models import RoleAssignmentCreateParameters

logger = logging.getLogger("Babylon")


class AzureIamService:

    def set(
        self,
        context: dict,
        principal_id: str,
        principal_type: str,
        resource_name: str,
        resource_type: str,
        role_id: str,
        iam_client: AuthorizationManagementClient,
    ):
        organization_id = context["api_organization_id"]
        workspace_key = context["api_workspace_key"]
        azure_subscription = context["azure_subscription_id"]
        resource_group_name = context["azure_resource_group_name"]
        principal_id = principal_id or context["platform_principal_id"]

        resource_name = (
            resource_name or f"{organization_id.lower()}-{workspace_key.lower()}"
        )
        prefix = f"/subscriptions/{azure_subscription}"
        scope = f"{prefix}/resourceGroups/{resource_group_name}/providers/{resource_type}/{resource_name}"
        role = f"{prefix}/providers/Microsoft.Authorization/roleDefinitions/{role_id}"
        try:
            iam_client.role_assignments.create(
                scope=scope,
                role_assignment_name=str(uuid.uuid4()),
                parameters=RoleAssignmentCreateParameters(
                    role_definition_id=role,
                    principal_id=principal_id,
                    principal_type=principal_type,
                ),
            )
        except Exception as e:
            logger.error(f"Failed to assign a new role: {e}")
