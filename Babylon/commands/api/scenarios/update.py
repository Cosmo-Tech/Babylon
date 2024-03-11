import pathlib
from logging import getLogger
from typing import Any

from click import command, option, Path, argument

from Babylon.commands.api.scenarios.services.api import ScenarioService
from Babylon.utils.credentials import pass_azure_token
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
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--scenario-id", type=str)
@argument("payload_file", type=Path(path_type=pathlib.Path))
def update(
    state: Any,
    organization_id: str,
    workspace_id: str,
    scenario_id: str,
    azure_token: str,
    payload_file: pathlib.Path,
) -> CommandResponse:
    """
    Update a scenario
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    service_state["api"]["scenario_id"] = (scenario_id or state["services"]["api"]["scenario_id"])

    if not payload_file.exists():
        print(f"file {payload_file} not found in directory")
        return CommandResponse.fail()
    spec = dict()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template(data=f.read(), state=state)

    scenario_service = ScenarioService(state=service_state, spec=spec, azure_token=azure_token)
    response = scenario_service.update()
    if response is None:
        return CommandResponse.fail()
    scenario = response.json()
    logger.info(f'Scenario {service_state["api"]["scenario_id"]} successfully updated')
    if service_state["api"]["scenario_id"] == state["services"]["api"]["scenario_id"]:
        logger.info(f'Scenario {state["services"]["api"]["scenario_id"]} stored in state has been successfully updated')
    return CommandResponse.success(scenario, verbose=True)
