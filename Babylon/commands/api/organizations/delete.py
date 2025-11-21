from logging import getLogger
from typing import Any

from click import command, echo, option, style

from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@option("--organization-id", "organization_id", type=str)
@retrieve_state
def delete(state: Any, keycloak_token: str, organization_id: str, force_validation: bool = False) -> CommandResponse:
    """Delete an organization"""
    _org = [""]
    _org.append("Delete organization")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    service = OrganizationService(state=state["services"], keycloak_token=keycloak_token)
    logger.info("Deleting organization")
    response = service.delete(force_validation=force_validation)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Organization {[service_state['api']['organization_id']]} successfully deleted")
    service_state["api"]["organization_id"] = ""
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    return CommandResponse.success(response)
