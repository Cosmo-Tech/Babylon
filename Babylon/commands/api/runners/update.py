import pathlib
from logging import getLogger
from typing import Any

from click import command, option, Path, argument

from Babylon.commands.api.runners.services.runner_api_svc import RunnerService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_state,
    output_to_file,
)
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@retrieve_state
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--runner-id", type=str)
@argument("payload_file", type=Path(path_type=pathlib.Path))
def update(
    state: Any,
    organization_id: str,
    workspace_id: str,
    runner_id: str,
    keycloak_token: str,
    payload_file: pathlib.Path,
) -> CommandResponse:
    """
    Update a runner
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    service_state["api"]["runner_id"] = (runner_id or state["services"]["api"]["runner_id"])

    if not payload_file.exists():
        print(f"file {payload_file} not found in directory")
        return CommandResponse.fail()
    spec = dict()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)

    runner_service = RunnerService(state=service_state, spec=spec, keycloak_token=keycloak_token)
    response = runner_service.update()
    if response is None:
        return CommandResponse.fail()
    runner = response.json()
    logger.info(f'Scenario {service_state["api"]["runner_id"]} successfully updated')
    if service_state["api"]["runner_id"] == state["services"]["api"]["runner_id"]:
        logger.info(f'Scenario {state["services"]["api"]["runner_id"]} stored in state has been successfully updated')
    return CommandResponse.success(runner, verbose=True)
