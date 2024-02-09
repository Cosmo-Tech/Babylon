from logging import getLogger
from typing import Any
from click import argument, command
from click import option
from Babylon.utils.decorators import retrieve_state, timing_decorator
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.messages import SUCCESS_DELETED
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.services.organizations_service import OrganizationsService

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@pass_azure_token("csm_api")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("id", type=str, required=False)
@retrieve_state
def delete(state: Any, azure_token: str, id: str, force_validation: bool = False) -> CommandResponse:
    """Delete an organization"""
    organizations_service = OrganizationsService(state['services'], azure_token)
    response = organizations_service.delete(id, force_validation)
    if response is None:
        return CommandResponse.fail()
    try:
        response.json()['organization_id']
    except KeyError:
        logger.error("Organization id is missing in response")

    logger.info(SUCCESS_DELETED("organization", response.json()['organization_id']))
    return CommandResponse.success()
