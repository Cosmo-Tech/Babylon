import pathlib
import json

from logging import getLogger
from typing import Any
from click import argument, command, echo, style
from click import Path
from Babylon.utils.decorators import injectcontext
from Babylon.utils.decorators import retrieve_state
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
@retrieve_state
def create(state: Any, keycloak_token: str, payload_file: pathlib.Path) -> CommandResponse:
    """
    Register new organization
    """
    _org = [""]
    _org.append("Register new organization")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    spec = dict()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    organizations_service = OrganizationService(state=state['services'], keycloak_token=keycloak_token, spec=spec)
    logger.info("[api] Creating organization")
    response = organizations_service.create()
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    state["services"]["api"]["organization_id"] = organization.get("id")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    logger.info(json.dumps(organization, indent=2))
    logger.info(f"[api] Organization {[organization.get('id')]} successfully created")
    return CommandResponse.success(organization)
