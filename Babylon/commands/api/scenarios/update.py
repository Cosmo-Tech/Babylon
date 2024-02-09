import pathlib
from logging import getLogger
from typing import Any, Optional

from click import command, option, Path

from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@retrieve_state
@pass_azure_token("csm_api")
@timing_decorator
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--scenario-id", type=str)
@option(
    "--payload",
    "payload",
    type=Path(path_type=pathlib.Path),
    help="Your custom scenario description file (yaml or json)",
    required=False,
)
def update(
    state: Any,
    organization_id: str,
    workspace_id: str,
    scenario_id: str,
    azure_token: str,
    payload: Optional[pathlib.Path] = None,
) -> CommandResponse:
    """
    Update a scenario
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    service_state["api"]["scenario_id"] = (scenario_id or state["services"]["api"]["scenario_id"])

    details = env.fill_template(payload)

    scenario_service = ScenarioService(state=service_state, spec=details, azure_token=azure_token)
    response = scenario_service.update()
    if response is None:
        return CommandResponse.fail()
    scenario = response.json()
    if scenario_id:
        state["services"]["api"]["scenario_id"] = scenario["id"]
        env.store_state_in_local(state)
        env.store_state_in_cloud(state)
        logger.info(f"Scenario {scenario['id']} has been successfully added in state")
    return CommandResponse.success(scenario, verbose=True)
