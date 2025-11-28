from logging import getLogger
from typing import Any
from click import command, option, echo, style, argument
from Babylon.utils.environment import Environment
from Babylon.commands.api.runs.services.run_api_svc import RunService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, retrieve_config_state, output_to_file
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@argument("runner_id", required=True)
@argument("run_id", required=True)
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@retrieve_config_state
def delete(
    state: Any,
    config: Any,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    runner_id: str,
    run_id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete the run

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace      
       RUNNER_ID : The unique identifier of the runner            
       RUN_ID: The unique identifier of the run
    """
    _run = [""]
    _run.append("Delete the Run")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state['organization_id'] = organization_id or services_state['organization_id']
    services_state["workspace_id"] = (workspace_id or services_state["workspace_id"])
    services_state["runner_id"] = (runner_id or services_state["runner_id"])
    services_state['run_id'] = run_id or services_state.get('run_id')
    service = RunService(state=services_state, keycloak_token=keycloak_token, config=config)
    logger.info(f"Deleting run {[services_state['run_id']]}")
    response = service.delete(force_validation=force_validation)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Run {[services_state['run_id']]} successfully deleted")
    return CommandResponse.success(response)
