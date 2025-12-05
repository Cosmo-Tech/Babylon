import pathlib
from logging import getLogger
from typing import Any

from click import Path, argument, command, echo, style

from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_state
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
def create(state: Any, config: Any, keycloak_token: str, payload_file: pathlib.Path) -> CommandResponse:
    """
    Register new organization

    Args:

       PAYLOAD_FILE : Path to the manifest file used to create the organization
    """
    _org = [""]
    _org.append("Register new organization")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    spec = dict()
    with open(payload_file, "r") as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    services_state = state["services"]["api"]
    organizations_service = OrganizationService(
        state=services_state, config=config, keycloak_token=keycloak_token, spec=spec
    )
    logger.info("Creating organization")
    response = organizations_service.create()
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    state["services"]["api"]["organization_id"] = organization.get("id")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    logger.info(f"Organization {[organization.get('id')]} successfully created")
    return CommandResponse.success(organization)
