import pathlib
from logging import getLogger
from typing import Any, Optional

from click import command, option, Path

from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED
from Babylon.utils.response import CommandResponse

env = Environment()
logger = getLogger("Babylon")


@command()
@wrapcontext()
@retrieve_state
@pass_azure_token("csm_api")
@timing_decorator
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option(
    "--payload",
    "payload",
    type=Path(path_type=pathlib.Path),
    help="Your custom scenario description file (yaml or json)",
    required=False,
)
def create(
    state: Any,
    organization_id: str,
    workspace_id: str,
    azure_token: str,
    payload: Optional[pathlib.Path] = None,
) -> CommandResponse:
    """
    Create new scenario
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])

    details = env.fill_template(payload)

    scenario_service = ScenarioService(state=service_state, azure_token=azure_token, spec=details)
    response = scenario_service.create()
    if response is None:
        return CommandResponse.fail()
    scenario = response.json()

    if organization_id:
        state["services"]["api"]["organization_id"] = organization_id
        env.store_state_in_local(state)
        env.store_state_in_cloud(state)
        logger.info(SUCCESS_CONFIG_UPDATED("api", "organization_id"))

    if workspace_id:
        state["services"]["api"]["workspace_id"] = workspace_id
        env.store_state_in_local(state)
        env.store_state_in_cloud(state)
        logger.info(SUCCESS_CONFIG_UPDATED("api", "workspace_id"))

    state["services"]["api"]["scenario_id"] = scenario["id"]
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)
    logger.info(f"Scenario {scenario['id']} has been successfully added in state")
    return CommandResponse.success(scenario, verbose=True)
