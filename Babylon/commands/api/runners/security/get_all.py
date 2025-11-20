from logging import getLogger
from typing import Any
from click import command, option, echo, style
from Babylon.commands.api.runners.services.runner_security_svc import (
    RunnerSecurityService, )
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    retrieve_state,
    injectcontext,
)
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--runner-id", "runner_id", type=str)
@retrieve_state
def get_all(
    state: Any,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    runner_id: str,
) -> CommandResponse:
    """
    Get all runner RBAC access
    """
    _run = [""]
    _run.append("Get all RBAC access to the Runner")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or state["services"]["api"]["workspace_id"]
    service_state["api"]["runner_id"] = runner_id or state["services"]["api"]["runner_id"]
    service = RunnerSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"Retrieving all RBAC access to the runner {[service_state['api']['runner_id']]}")
    response = service.get_all()
    if response is None:
        return CommandResponse.fail()
    runner_security = response.json()
    logger.info("Successfully retrieved all RBAC access to the runner")
    return CommandResponse.success(runner_security)
