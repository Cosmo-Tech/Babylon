from logging import getLogger
from typing import Any
from Babylon.utils.environment import Environment
from click import command, option, echo, style
from Babylon.commands.api.solutions.services.solutions_api_svc import SolutionService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@retrieve_state
def delete(
    state: Any,
    keycloak_token: str,
    organization_id: str,
    solution_id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete a solution
    """
    _sol = [""]
    _sol.append("Delete solution")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["solution_id"] = (solution_id or service_state["api"]["solution_id"])
    solutions_service = SolutionService(state=service_state, keycloak_token=keycloak_token)
    logger.info("[api] Deleting solution")
    response = solutions_service.delete(force_validation=force_validation)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"[api] Solution {[service_state['api']['solution_id']]} successfully deleted")
    state["services"]["api"]["solution_id"] = ""
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    return CommandResponse.success(response)
