import pathlib
from logging import getLogger
from typing import Any
from click import Path, argument, command, echo, style
from Babylon.utils.decorators import retrieve_config_state
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_config_state

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@argument("organization_id", required=True)
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
@retrieve_config_state
def update(state: Any, config: Any, keycloak_token: str, organization_id: str,
           payload_file: pathlib.Path) -> CommandResponse:
    """
    Update a specific organization.

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       PAYLOAD_FILE : Path to the manifest file used to update the organization
    """
    _org = [""]
    _org.append("Update a specific organization")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    spec = dict()
    with open(payload_file, "r") as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    services_state = state["services"]["api"]
    services_state["organization_id"] = (organization_id or services_state["organization_id"])
    organizations_service = OrganizationService(state=services_state,
                                                config=config,
                                                keycloak_token=keycloak_token,
                                                spec=spec)
    logger.info(f"Updating organization {[services_state['organization_id']]}")
    response = organizations_service.update()
    if response is None:
        return CommandResponse.fail()
    organization = response.json()
    logger.info(f"Organization {[organization.get('id')]} successfully updated")
    return CommandResponse.success(organization)
