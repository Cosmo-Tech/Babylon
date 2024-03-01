from logging import getLogger
from typing import Any
from click import argument, command
from Babylon.commands.api.organizations.services.security import OrganizationSecurityService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@argument("identity_id", type=str)
@retrieve_state
def get(state: Any, azure_token: str, identity_id: str) -> CommandResponse:
    """
    Get organization user RBAC access
    """
    service_state = state["services"]
    service = OrganizationSecurityService(azure_token=azure_token, state=service_state)
    response = service.get(id=identity_id)
    rbac = response.json()
    return CommandResponse.success(rbac, verbose=True)
