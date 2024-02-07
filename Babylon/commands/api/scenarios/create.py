import json
from typing import Any

from click import command, option

from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext, retrieve_state
from Babylon.utils.response import CommandResponse

payload = json.dumps({
    "name": "Creating scenario with Babylon",
    "description": "Brewery master reference analysis",
    "tags": ["Brewery", "reference"],
    "runTemplateId": "hundred",
    "security": {
        "default": "viewer",
        "accessControlList": [{
            "id": "elena.sasova@cosmotech.com",
            "role": "admin"
        }],
    },
})


@command()
@wrapcontext()
@retrieve_state
@pass_azure_token("csm_api")
@timing_decorator
@option("--organization_id", "organization_id", type=str)
@option("--workspace_id", "workspace_id", type=str)
def create(state: Any, organization_id: str, workspace_id: str, azure_token: str) -> CommandResponse:
    """
    Create new scenario
    """
    service_state = state["state"]
    if organization_id:
        service_state["api"]["organization_id"] = organization_id
    if workspace_id:
        service_state["api"]["workspace_id"] = workspace_id

    # change this line when scenario manipulation is specified
    spec = payload

    scenario_service = ScenarioService(state=service_state, azure_token=azure_token, spec=spec)
    response = scenario_service.create()
    if response is None:
        return CommandResponse.fail()
    scenario = response.json()
    return CommandResponse.success(scenario, verbose=True)
