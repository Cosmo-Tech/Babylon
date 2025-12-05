import json
from logging import getLogger
from typing import Any

from click import argument, command, echo, option, style

from Babylon.commands.api.runners.services.runner_security_svc import (
    RunnerSecurityService,
)
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    injectcontext,
    output_to_file,
    retrieve_state,
)
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option(
    "--role",
    "role",
    type=str,
    required=True,
    help="Role RBAC",
)
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@argument("runner_id", required=True)
@retrieve_state
def set_default(
    state: Any,
    config: Any,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    runner_id: str,
    role: str = None,
) -> CommandResponse:
    """
    Set the runner default security

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
       RUNNER_ID : The unique identifier of the runner
    """
    _run = [""]
    _run.append("Set default RBAC access to the runner")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    services_state["runner_id"] = runner_id or services_state["runner_id"]
    service = RunnerSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    details = json.dumps(obj={"role": role}, indent=2, ensure_ascii=True)
    logger.info(f"Setting default RBAC access to the runner {[services_state['runner_id']]}")
    response = service.set_default(details)
    if response is None:
        return CommandResponse.fail()
    default_security = response.json()
    logger.info(f"default RBAC access successfully set with role {[role]}")
    return CommandResponse.success(default_security)
