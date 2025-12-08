from logging import getLogger
from typing import Any

from click import argument, command, echo, option, style

from Babylon.commands.api.datasets.services.datasets_security_svc import DatasetSecurityService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@argument("dataset_id", required=True)
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_state
def get(
    state: Any, config: Any, keycloak_token: str, email: str, organization_id: str, workspace_id: str, dataset_id: str
) -> CommandResponse:
    """
    Get dataset user RBAC access

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
       DATASET_ID: The unique identifier of the datatset
    """
    _data = [""]
    _data.append(" Get dataset user RBAC access")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    services_state["dataset_id"] = dataset_id or services_state["dataset_id"]
    service = DatasetSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Get user {[email]} RBAC access to the dataset {[services_state['dataset_id']]}")
    response = service.get(id=email)
    if response is None:
        return CommandResponse.fail()
    rbac = response.json()
    return CommandResponse.success(rbac)
