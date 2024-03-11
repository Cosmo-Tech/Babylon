from logging import getLogger
from typing import Any
from click import argument, command
from Babylon.commands.api.workspaces.services.security import (
    ApiWorkspaceSecurityService, )
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
@argument("identity_id", type=str)
@retrieve_state
def get(state: Any, azure_token: str, identity_id: str) -> CommandResponse:
    """
    Get workspace users RBAC access
    """
    service_state = state["services"]
    service = ApiWorkspaceSecurityService(azure_token=azure_token, state=service_state)
    response = service.get(id=identity_id)
    return CommandResponse.success(response, verbose=True)
