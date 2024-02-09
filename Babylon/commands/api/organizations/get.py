from logging import getLogger
from typing import Any
from click import argument, option
from click import command
from Babylon.utils.typing import QueryType
from Babylon.utils.decorators import retrieve_state, timing_decorator
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.services.organizations_service import OrganizationsService

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--select", "select", is_flag=True, default=True, help="Save this organization in configuration")
@argument("id", type=QueryType(), required=False)
@retrieve_state
def get(state: Any, id: str, azure_token: str) -> CommandResponse:
    """Get an organization details"""
    organizations_service = OrganizationsService(state['services'], azure_token)
    response = organizations_service.get()
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)
    return CommandResponse.success(organization, verbose=True)
