import json
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
@option(
    "--role",
    "role",
    type=str,
    required=True,
    help="Role RBAC",
)
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_state
def update(state: dict, keycloak_token: str, email: str, role: str) -> CommandResponse:
    """
    Update organization users RBAC access
    """
    _ret = [""]
    _ret.append("Update organization user RBAC access")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    details = json.dumps({"id": email, "role": role})
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=service_state)
    org_id = service_state["api"]["organization_id"]
    logger.info(f"[api] Updating user {email} RBAC access in the organization {org_id}")
    response = service.update(id=email, details=details)
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info(json.dumps(rbacs, indent=2))
    logger.info(f"[api] User {email} RBAC access successfully Updated")
    return CommandResponse.success()
