import pathlib

from logging import getLogger
from typing import Any
from click import argument, command
from click import Path
from Babylon.utils.decorators import injectcontext, timing_decorator
from Babylon.utils.decorators import retrieve_state
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.services.organizations_service import OrganizationService

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
@retrieve_state
def create(
    state: Any,
    azure_token: str,
    payload_file: pathlib.Path,
) -> CommandResponse:
    """
    Register new organization
    """
    spec = dict()
    spec["payload"] = env.fill_template(payload_file)
    organizations_service = OrganizationService(state['services'], azure_token, spec=spec)
    response = organizations_service.create()
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    state["services"]["api"]["organization_id"] = organization.get("id")
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)
    logger.info(f"Organization {organization.get('id')} successfully saved in state {state.get('id')}")
    return CommandResponse.success(organization, verbose=True)
