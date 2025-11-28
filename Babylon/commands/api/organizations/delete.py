from logging import getLogger
from typing import Any
from click import command, argument, option, echo, style
from Babylon.utils.decorators import injectcontext, retrieve_config_state
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("organization_id", required=True)
@retrieve_config_state
def delete(state: Any,
           config: Any,
           keycloak_token: str,
           organization_id: str,
           force_validation: bool = False) -> CommandResponse:
    """
    Delete a specific organization

    Args:

       ORGANIZATION_ID: The unique identifier of the organization
    """
    _org = [""]
    _org.append("Delete a specific organization")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = (organization_id or services_state["organization_id"])
    service = OrganizationService(state=services_state, config=config, keycloak_token=keycloak_token)
    logger.info("Deleting organization")
    response = service.delete(force_validation=force_validation)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Organization {[services_state['organization_id']]} successfully deleted")
    state["services"]["api"]["organization_id"] = ""
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    return CommandResponse.success(response)
