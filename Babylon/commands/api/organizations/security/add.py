import json
import click
from logging import getLogger
from typing import Any
from click import command
from click import option
from Babylon.commands.api.organizations.services.organization_security_svc import (
    OrganizationSecurityService, )
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    retrieve_state,
    injectcontext,
)
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--role", "role", type=str, required=True, help="Role RBAC")
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_state
def add(state: Any, keycloak_token: str, email: str, role: str = None) -> CommandResponse:
    """
    Add organization users RBAC access
    """
    _ret = [""]
    _ret.append("Add organization user RBAC access")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=service_state)
    details = json.dumps(obj={"id": email, "role": role}, indent=2, ensure_ascii=True)
    logger.info(f"[api] Adding user {email} RBAC access to the organization {service_state["api"]["organization_id"]}")
    response = service.add(details)
    if response: 
        rbacs = response.json()
        logger.info(json.dumps(rbacs, indent=2))
        logger.info("[api] User RBAC access successfully added")
    return CommandResponse.success()
