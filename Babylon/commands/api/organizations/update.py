import pathlib

from logging import getLogger
from typing import Any
from click import Path, argument, command
from Babylon.utils.decorators import retrieve_state, timing_decorator
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
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
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
@retrieve_state
def update(state: Any, azure_token: str, payload_file: pathlib.Path) -> CommandResponse:
    """
    Update an organization
    """
    service_state = state["services"]
    spec = dict()
    spec["payload"] = env.fill_template(payload_file)
    organizations_service = OrganizationService(state=service_state, azure_token=azure_token, spec=spec)
    response = organizations_service.update()
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    if response:
        org_id = service_state["api"]["organization_id"]
        logger.info(f"Organization {org_id} successfully updated")
        if org_id == state["services"]["api"]["workspace_id"]:
            logger.info(f"Organization {org_id} stored in state has been successfully updated")
    return CommandResponse.success(organization, verbose=True)
