import logging
import click

from click import command, option
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import output_to_file, retrieve_state
from Babylon.commands.api.organizations.services.organization_security_svc import (
    OrganizationSecurityService, )

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@output_to_file
@option("--organization-id", "organization_id", type=str)
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_state
def delete(state: dict, keycloak_token: str, email: str, organization_id: str) -> CommandResponse:
    """
    Delete organization users RBAC access
    """
    _ret = [""]
    _ret.append("Delete organization user RBAC access")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(
        f"[api] Deleting user {email} RBAC access from the organization {service_state['api']['organization_id']}")
    response = service.delete(id=email)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"[api] User {email} RBAC access successfully deleted")
    return CommandResponse.success(response)
