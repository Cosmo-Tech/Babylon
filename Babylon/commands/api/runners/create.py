import pathlib
from logging import getLogger
from typing import Any

from click import command, option, Path, argument

from Babylon.commands.api.runners.services.runner_api_svc import RunnerService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_state,
    output_to_file,
)
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

env = Environment()
logger = getLogger("Babylon")


@command()
@injectcontext()
@retrieve_state
@pass_azure_token("csm_api")
@output_to_file
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@argument(
    "payload_file",
    type=Path(path_type=pathlib.Path),
)
def create(
    state: Any,
    organization_id: str,
    workspace_id: str,
    azure_token: str,
    payload_file: pathlib.Path,
) -> CommandResponse:
    """
    Create new scenario
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])

    if not payload_file.exists():
        print(f"file {payload_file} not found in directory")
        return CommandResponse.fail()
    spec = dict()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template(data=f.read(), state=state)

    scenario_service = RunnerService(state=service_state, azure_token=azure_token, spec=spec)
    response = scenario_service.create()
    if response is None:
        return CommandResponse.fail()
    scenario = response.json()

    state["services"]["api"]["scenario_id"] = scenario["id"]
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    logger.info(f"Scenario {scenario['id']} has been successfully added in state")
    return CommandResponse.success(scenario, verbose=True)
