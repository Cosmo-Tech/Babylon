import logging
import click

from click import argument, command
from Babylon.commands.api.workspaces.services.workspaces_security_svc import ApiWorkspaceSecurityService
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import output_to_file, retrieve_state

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@output_to_file
@argument("id", type=str)
@retrieve_state
def delete(state: dict, keycloak_token: str, id: str) -> CommandResponse:
    """
    Delete workspace users RBAC access
    """
    _ret = [""]
    _ret.append("Delete workspace users RBAC access")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    service = ApiWorkspaceSecurityService(keycloak_token=keycloak_token, state=service_state)
    response = service.delete(id=id)
    logger.info(response)
    return CommandResponse.success(response, verbose=True)
