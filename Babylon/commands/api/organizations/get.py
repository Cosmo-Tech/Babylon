from logging import getLogger
from typing import Any
from click import option
from click import command
from Babylon.utils.decorators import retrieve_state, timing_decorator
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.services.organizations_service import OrganizationService

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@retrieve_state
def get(state: Any, organization_id: str, azure_token: str) -> CommandResponse:
    """Get an organization details"""
    services_state = state["services"]
    services_state["api"]["organization_id"] = (organization_id or services_state["api"]["organization_id"])
    organizations_service = OrganizationService(state=services_state, azure_token=azure_token)
    response = organizations_service.get()
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    return CommandResponse.success(organization, verbose=True)
