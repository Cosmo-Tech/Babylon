import pathlib
from logging import getLogger
from typing import Any
from click import argument, command, echo, style, Path
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_config_state

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config_state
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
def create(state: Any, keycloak_token: str, payload_file: pathlib.Path) -> CommandResponse:
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
    organizations_service = OrganizationService(state=state["services"], keycloak_token=keycloak_token, spec=spec)
    logger.info("Creating organization")
    response = organizations_service.create()
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    logger.info(f"Organization {[organization.get('id')]} successfully created")
    return CommandResponse.success(organization)
