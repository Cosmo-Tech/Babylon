from logging import getLogger
from typing import Any
from click import command, argument
from click import option
from Babylon.commands.api.runners.services.runner_security_svc import (
    RunnerSecurityService, )
from Babylon.utils.credentials import pass_azure_token
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
@pass_azure_token("csm_api")
@argument("identity_id", type=str)
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--runner-id", "runner_id", type=str)
@retrieve_state
def delete(
    state: Any,
    azure_token: str,
    identity_id: str,
    organization_id: str,
    workspace_id: str,
    runner_id: str,
) -> CommandResponse:
    """
    Delete runner RBAC access
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or state["services"]["api"]["workspace_id"]
    service_state["api"]["runner_id"] = runner_id or state["services"]["api"]["runner_id"]
    service = RunnerSecurityService(azure_token=azure_token, state=service_state)
    service.delete(id=identity_id)
    return CommandResponse.success()
