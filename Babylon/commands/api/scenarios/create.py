import json

from click import command

from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.utils.credentials import get_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext
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
@timing_decorator
def create() -> CommandResponse:
    """
    Create new scenario
    """

    token = get_azure_token("csm_api")

    state = {
        "api_url": "https://dev.api.cosmotech.com",
        "organizationId": "o-3z188zr63xk",
        "workspaceId": "w-k91e49pgyw6",
        "azure_token": token,
    }
    spec = payload

    service = ScenarioService(state=state, spec=spec)
    response = service.create()
    if response is None:
        return CommandResponse.fail()
    return CommandResponse.success(response.json(), verbose=True)
