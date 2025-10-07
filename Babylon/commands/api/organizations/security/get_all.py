import click
import json

from logging import getLogger
from typing import Any
from click import command
from Babylon.commands.api.organizations.services.organization_security_svc import OrganizationSecurityService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_state
def get_all(state: Any, keycloak_token: str) -> CommandResponse:
    """
    Get all RBAC access to the organization
    """
    _ret = [""]
    _ret.append("Get all RBAC access to the organization")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"[api] Retrieving all RBAC access to the organization {service_state['api']['organization_id']}")
    response = service.get_all()
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info(json.dumps(rbacs, indent=2))
    return CommandResponse.success()
