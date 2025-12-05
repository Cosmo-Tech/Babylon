from logging import getLogger
from typing import Any

from click import argument, command, echo, option, style

from Babylon.commands.api.runners.services.runner_api_svc import RunnerService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@argument("runner_id", required=True)
@option("-D", "force_validation", is_flag=True, help="Force Delete")
def delete(
    state: Any,
    config: Any,
    organization_id: str,
    workspace_id: str,
    keycloak_token: str,
    runner_id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete a runner

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
       RUNNER_ID : The unique identifier of the runner
    """
    _run = [""]
    _run.append("Delete a runner")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    services_state["runner_id"] = runner_id or services_state["runner_id"]
    runner_service = RunnerService(state=services_state, keycloak_token=keycloak_token, config=config)
    logger.info("Deleting runner")
    response = runner_service.delete(force_validation=force_validation)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Runner {[services_state['runner_id']]} successfully deleted")
    state["services"]["api"]["runner_id"] = ""
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    return CommandResponse.success(response)
