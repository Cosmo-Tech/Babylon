import json
import click

from logging import getLogger
from typing import Any
from click import option
from click import command
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
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
@retrieve_state
def get(state: Any, organization_id: str, keycloak_token: str) -> CommandResponse:
    """Get an organization details"""
    _ret = [""]
    _ret.append("Get organization details")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    services_state = state["services"]
    services_state["api"]["organization_id"] = (organization_id or services_state["api"]["organization_id"])
    organizations_service = OrganizationService(state=state['services'], keycloak_token=keycloak_token)
    logger.info(f"[api] Retrieving organization {services_state["api"]["organization_id"]} details")
    response = organizations_service.get()
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    logger.info(json.dumps(organization, indent=2))
    return CommandResponse.success()
