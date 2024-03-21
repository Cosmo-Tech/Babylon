from logging import getLogger
from typing import Any
from click import command
from click import option
from Babylon.commands.api.scenarios.services.scenario_security_svc import (
    ScenarioSecurityService, )
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import (
    retrieve_state,
    injectcontext,
)
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--scenario-id", "scenario_id", type=str)
@retrieve_state
def get_all(
    state: Any,
    azure_token: str,
    organization_id: str,
    workspace_id: str,
    scenario_id: str,
) -> CommandResponse:
    """
    Get all scenario RBAC access
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or state["services"]["api"]["workspace_id"]
    service_state["api"]["scenario_id"] = scenario_id or state["services"]["api"]["scenario_id"]
    service = ScenarioSecurityService(azure_token=azure_token, state=service_state)
    response = service.get_all()
    scenario_security = response.json()
    if response is None:
        return CommandResponse.fail()
    return CommandResponse.success(scenario_security, verbose=True)
