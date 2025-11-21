import json
from logging import getLogger
from typing import Any

from click import command, echo, option, style

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
@option("--role", "role", type=str, required=True, help="Role RBAC")
@option("--email", "email", type=str, required=True, help="Valid email")
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--runner-id", "runner_id", type=str)
@retrieve_state
def add(
    state: Any,
    keycloak_token: str,
    email: str,
    organization_id: str,
    workspace_id: str,
    runner_id: str,
    role: str = None,
) -> CommandResponse:
    """
    Add runner users RBAC access
    """
    _run = [""]
    _run.append("Add a runner users RBAC access")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or state["services"]["api"]["workspace_id"]
    service_state["api"]["runner_id"] = runner_id or state["services"]["api"]["runner_id"]
    service = RunnerSecurityService(keycloak_token=keycloak_token, state=service_state)
    details = json.dumps(obj={"id": email, "role": role}, indent=2, ensure_ascii=True)
    logger.info(f"Granting user {[email]} RBAC permissions on runner {[service_state['api']['runner_id']]}")
    response = service.add(details)
    if response is None:
        return CommandResponse.fail()
    runner_security = response.json()
    logger.info("[User RBAC permissions successfully added")
    return CommandResponse.success(runner_security)
