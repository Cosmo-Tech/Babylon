import logging

from typing import Any, Optional
from azure.mgmt.authorization import AuthorizationManagementClient
from click import Choice, option
from click import command
from Babylon.commands.azure.permission.service.api import AzureIamService
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType
from Babylon.utils.clients import (
    pass_iam_client,
)

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_iam_client
@option(
    "--resource-type", "resource_type", type=QueryType(), help="Ressource Type Id Azure"
)
@option(
    "--resource-name", "resource_name", type=QueryType(), help="Ressource Name Azure"
)
@option(
    "--principal-type",
    "principal_type",
    type=Choice(["User", "Group", "ServicePrincipal", "ForeignGroup", "Device"]),
    default="ServicePrincipal",
    help="Principal Type Azure",
)
@option(
    "--principal-id",
    "principal_id",
    type=QueryType(),
    required=True,
    help="Principal Id Ressource",
)
@option(
    "--role-id", "role_id", type=QueryType(), required=True, help="Role Id Ressource"
)
@inject_context_with_resource(
    {
        "api": ["organization_id", "workspace_key"],
        "azure": ["resource_group_name", "subscription_id"],
        "platform": ["principal_id"],
    }
)
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
    apiIam = AzureIamService()
    apiIam.set(
        context=context,
        principal_id=principal_id,
        principal_type=principal_type,
        resource_type=resource_type,
        resource_name=resource_name,
        role_id=role_id,
        iam_client=iam_client
    )
    return CommandResponse.success()
