import click
import json

from logging import getLogger
from typing import Any
from click import option, command
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
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_state
def get(state: Any, keycloak_token: str, email: str) -> CommandResponse:
    """
    Get organization user RBAC access
    """
    _ret = [""]
    _ret.append("Get organization user RBAC access")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"[api] Get user {email} RBAC access to the organization {service_state['api']['organization_id']}")
    response = service.get(id=email)
    if response is None:
        return CommandResponse.fail()
    rbac = response.json()
    logger.info(json.dumps(rbac, indent=2))
    return CommandResponse.success(rbac)
