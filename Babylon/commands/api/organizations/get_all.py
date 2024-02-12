import jmespath

from logging import getLogger
from typing import Any
from click import command
from click import option
from Babylon.utils.decorators import retrieve_state, timing_decorator
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.services.organizations_service import OrganizationsService

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any, azure_token: str, filter: str) -> CommandResponse:
    """
    Get all organization details
    """
    service_state = state["services"]
    organization_service = OrganizationsService(state=service_state, azure_token=azure_token)
    response = organization_service.get_all()
    if response is None:
        return CommandResponse.fail()
    organizations = response.json()
    if len(organizations) and filter:
        organizations = jmespath.search(filter, organizations)
    return CommandResponse.success(organizations, verbose=True)
