import pathlib
from logging import getLogger
from typing import Any

from click import Path, argument, command, echo, style

from Babylon.commands.api.runners.services.runner_api_svc import RunnerService
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
@retrieve_state
@output_to_file
@pass_keycloak_token()
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@argument("runner_id", required=True)
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
def update(
    state: Any,
    config: Any,
    organization_id: str,
    workspace_id: str,
    runner_id: str,
    keycloak_token: str,
    payload_file: pathlib.Path,
) -> CommandResponse:
    """
    Update a runner

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
       RUNNER_ID : The unique identifier of the runner
       PAYLOAD_FILE : Path to the manifest file used to update the runner
    """
    _run = [""]
    _run.append("Update a runner")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    spec = dict()
    with open(payload_file, "r") as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    runner_service = RunnerService(state=services_state, spec=spec, keycloak_token=keycloak_token, config=config)
    logger.info(f"Updating runner {[runner_id]}")
    response = runner_service.update(runner_id)
    if response is None:
        return CommandResponse.fail()
    runner = response.json()
    logger.info(f"Runner {[runner_id]} successfully updated")
    return CommandResponse.success(runner)
