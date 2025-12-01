from logging import getLogger
from typing import Any

from click import argument, command, echo, style

from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_config_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@argument("organization_id", required=True)
@retrieve_config_state
def get(state: Any, config: Any, organization_id: str, keycloak_token: str) -> CommandResponse:
    """
    Get the details of a specific organization.

    Args:

        ORGANIZATION_ID: The unique identifier of the organization
    """
    _org = [""]
    _org.append("Get a specific organization details")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    organizations_service = OrganizationService(state=services_state, config=config, keycloak_token=keycloak_token)
    response = organizations_service.get()
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    logger.info(f"Retrieved organization {[services_state['organization_id']]} details")
    return CommandResponse.success(organization)
