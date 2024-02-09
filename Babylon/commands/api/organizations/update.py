import pathlib

from logging import getLogger
from typing import Any, Optional
from click import Path, argument, command
from click import option
from Babylon.utils.decorators import retrieve_state, timing_decorator
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.messages import SUCCESS_UPDATED
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType
from Babylon.services.organizations_service import OrganizationsService

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--file",
        "organization_file",
        type=Path(path_type=pathlib.Path),
        help="Your custom organization description file (yaml or json)")
@argument("id", type=QueryType())
@retrieve_state
def update(state: Any, azure_token: str, id: str, organization_file: Optional[pathlib.Path]) -> CommandResponse:
    """
    Update an organization
    """
    organizations_service = OrganizationsService(state['services'], azure_token)
    response = organizations_service.update(id, organization_file)
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    logger.info(SUCCESS_UPDATED("organization", organization["id"]))
    return CommandResponse.success(organization, verbose=True)
