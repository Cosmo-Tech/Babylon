import json
import click
from logging import getLogger
from typing import Any
from click import argument, command
from Babylon.commands.api.workspaces.services.workspaces_security_svc import (
    ApiWorkspaceSecurityService, )
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
@argument("identity_id", type=str)
@retrieve_state
def get(state: Any, keycloak_token: str, identity_id: str) -> CommandResponse:
    """
    Get workspace users RBAC access
    """
    _ret = [""]
    _ret.append("Get workspace users RBAC access")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    service = ApiWorkspaceSecurityService(keycloak_token=keycloak_token, state=service_state)
    response = service.get(id=identity_id)
    logger.info(json.dumps(response.json(), indent=2))
    return CommandResponse.success(response)
