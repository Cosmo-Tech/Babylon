import pathlib
from logging import getLogger
from typing import Any
from click import command, Path, argument, echo, style
from Babylon.commands.api.runners.services.runner_api_svc import RunnerService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_config_state,
    output_to_file,
)
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

env = Environment()
logger = getLogger(__name__)


@command()
@injectcontext()
@retrieve_config_state
@pass_keycloak_token()
@output_to_file
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@argument(
    "payload_file",
    type=Path(path_type=pathlib.Path, exists=True),
)
def create(
    state: Any,
    config: Any,
    organization_id: str,
    workspace_id: str,
    keycloak_token: str,
    payload_file: pathlib.Path,
) -> CommandResponse:
    """
    Create new runner

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace      
       PAYLOAD_FILE : Path to the manifest file used to update the workspace
    """
    _run = [""]
    _run.append("Register new runner")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = (organization_id or services_state["organization_id"])
    services_state["workspace_id"] = (workspace_id or services_state["workspace_id"])
    spec = dict()
    with open(payload_file, "r") as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    runner_service = RunnerService(state=services_state, keycloak_token=keycloak_token, spec=spec, config=config)
    logger.info("Creating runner")
    response = runner_service.create()
    if response is None:
        return CommandResponse.fail()
    runner = response.json()
    services_state["runner_id"] = runner.get("id")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    logger.info(f"Runner {[runner['id']]} successfully created")
    return CommandResponse.success(runner)
