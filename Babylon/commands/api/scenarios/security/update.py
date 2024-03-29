import json
from logging import getLogger
from typing import Any
from click import command, argument
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
@argument("identity_id", type=str)
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
def update(
    state: Any,
    azure_token: str,
    identity_id: str,
    role: str,
    organization_id: str,
    workspace_id: str,
    scenario_id: str,
) -> CommandResponse:
    """
    Update scenario RBAC access for user
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or state["services"]["api"]["workspace_id"]
    service_state["api"]["scenario_id"] = scenario_id or state["services"]["api"]["scenario_id"]
    details = json.dumps({"id": identity_id, "role": role})
    service = ScenarioSecurityService(azure_token=azure_token, state=service_state)
    response = service.update(id=identity_id, details=details)
    scenario_security = response.json()
    if response is None:
        return CommandResponse.fail()
    return CommandResponse.success(scenario_security, verbose=True)
