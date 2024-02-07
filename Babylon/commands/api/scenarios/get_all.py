from click import command, option
from typing import Any

from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

env = Environment()


@command()
@wrapcontext()
@pass_azure_token("csm_api")
@timing_decorator
@option("--organization_id", "organization_id", type=str)
@option("--workspace_id", "workspace_id", type=str)
@retrieve_state
def get_all(state: Any, organization_id: str, workspace_id: str, azure_token: str) -> CommandResponse:
    """
    Get all scenarios in the workspace
    """

    service_state = state["state"]
    if organization_id:
        service_state["api"]["organization_id"] = organization_id
    if workspace_id:
        service_state["api"]["workspace_id"] = workspace_id

    scenario_service = ScenarioService(state=service_state, azure_token=azure_token)
    response = scenario_service.get_all()
    if response is None:
        return CommandResponse.fail()
    scenarios = response.json()
    return CommandResponse.success(scenarios, verbose=True)
