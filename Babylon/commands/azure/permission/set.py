import logging

from typing import Any, Optional
from azure.mgmt.authorization import AuthorizationManagementClient
from click import Choice, option
from click import command
from Babylon.commands.azure.permission.services.iam_api_svc import AzureIamService
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment

from Babylon.utils.clients import (
    pass_iam_client, )

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_iam_client
@option("--resource-type", "resource_type", type=str, help="Ressource Type Id Azure")
@option("--resource-name", "resource_name", type=str, help="Ressource Name Azure")
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
    type=str,
    required=True,
    help="Principal Id Ressource",
)
@option("--role-id", "role_id", type=str, required=True, help="Role Id Ressource")
@retrieve_state
def set(
    state: Any,
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
    service_state = state['services']
    service = AzureIamService(iam_client=iam_client, state=service_state)
    service.set(
        principal_id=principal_id,
        principal_type=principal_type,
        resource_type=resource_type,
        resource_name=resource_name,
        role_id=role_id,
    )
    return CommandResponse.success()
