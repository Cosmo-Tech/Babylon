import pathlib
import json
import click

from logging import getLogger
from typing import Any
from click import Path, argument, command, option
from Babylon.utils.decorators import retrieve_state
from Babylon.utils.decorators import injectcontext
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
@option("--organization-id", "organization_id", type=str)
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
@retrieve_state
def update(state: Any, keycloak_token: str, organization_id: str, payload_file: pathlib.Path) -> CommandResponse:
    """
    Update an organization
    """
    _ret = [""]
    _ret.append("Update an organization")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    spec = dict()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    organizations_service = OrganizationService(state=state['services'], keycloak_token=keycloak_token, spec=spec)
    logger.info(f"[api] Updating organization {state['services']['api']['organization_id']}")
    response = organizations_service.update()
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    logger.info(json.dumps(organization, indent=2))
    logger.info(f"[api] Organization {organization.get('id')} successfully updated")
    return CommandResponse.success(organization)
