import json
from logging import getLogger
from typing import Any
from click import command
from click import option
from Babylon.commands.api.scenarios.security.service.api import (
    ScenarioSecurityService, )
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import (
    retrieve_state,
    wrapcontext,
)
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option(
    "--role",
    "role",
    type=str,
    required=True,
    help="Role RBAC",
)
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--scenario-id", "scenario_id", type=str)
@retrieve_state
def set_default(
    state: Any,
    azure_token: str,
    organization_id: str,
    workspace_id: str,
    scenario_id: str,
    role: str = None,
) -> CommandResponse:
    """
    Add scenario users RBAC access
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or state["services"]["api"]["workspace_id"]
    service_state["api"]["scenario_id"] = scenario_id or state["services"]["api"]["scenario_id"]
    service = ScenarioSecurityService(azure_token=azure_token, state=service_state)
    details = json.dumps(obj={"role": role}, indent=2, ensure_ascii=True)
    response = service.set_default(details)
    default_security = response.json()
    if response is None:
        return CommandResponse.fail()
    return CommandResponse.success(default_security, verbose=True)
