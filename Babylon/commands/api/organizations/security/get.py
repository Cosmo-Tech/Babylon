from logging import getLogger
from typing import Any
from click import command
from Babylon.commands.api.organizations.security.service.api import ApiOrganizationSecurityService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@retrieve_state
def get(state: Any, azure_token: str) -> CommandResponse:
    """
    Update organization users RBAC access
    """
    service_state = state["services"]
    service = ApiOrganizationSecurityService(azure_token=azure_token, state=service_state)
    response = service.get()
    return CommandResponse.success(response, verbose=True)
