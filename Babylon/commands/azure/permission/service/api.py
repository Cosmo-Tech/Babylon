import logging
import uuid

from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.authorization.models import RoleAssignmentCreateParameters

logger = logging.getLogger("Babylon")


class AzureIamService:

    def __init__(self, iam_client: AuthorizationManagementClient, state: dict = None) -> None:
        self.state = state
        self.iam_client = iam_client

    def set(
        self,
        principal_id: str,
        resource_name: str,
        resource_type: str,
        role_id: str,
        principal_type: str = "ServicePrincipal",
    ):
        organization_id = self.state["api"]["organization_id"]
        workspace_key = self.state["api"]["workspace_key"]
        azure_subscription = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        principal_id = principal_id or self.state["platform"]["principal_id"]

        resource_name = (resource_name or f"{organization_id.lower()}-{workspace_key.lower()}")
        prefix = f"/subscriptions/{azure_subscription}"
        scope = f"{prefix}/resourceGroups/{resource_group_name}/providers/{resource_type}/{resource_name}"
        role = f"{prefix}/providers/Microsoft.Authorization/roleDefinitions/{role_id}"
        try:
            self.iam_client.role_assignments.create(
                scope=scope,
                role_assignment_name=str(uuid.uuid4()),
                parameters=RoleAssignmentCreateParameters(
                    role_definition_id=role,
                    principal_id=principal_id,
                    principal_type=principal_type,
                ),
            )
        except Exception as e:
            logger.info(e)
