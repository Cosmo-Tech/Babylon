from json import dumps
from logging import getLogger

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
@pass_keycloak_token()
@output_to_file
@option(
    "--role",
    "role",
    type=str,
    required=True,
    help="Role RBAC",
)
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@argument("dataset_id", required=True)
@retrieve_state
def set_default(
    state: dict, config: dict, keycloak_token: str, role: str, organization_id: str, workspace_id: str, dataset_id: str
) -> CommandResponse:
    """
    Set the dataset default security

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
       DATASET_ID: The unique identifier of the datatset
    """
    _data = [""]
    _data.append(" Set dataset default security RBAC")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    services_state["dataset_id"] = dataset_id or services_state["dataset_id"]
    details = dumps({"role": role})
    service = DatasetSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Setting default RBAC access to the dataset {[services_state['dataset_id']]}")
    response = service.set_default(details=details)
    if response is None:
        return CommandResponse.fail()
    default_security = response.json()
    logger.info(dumps(default_security, indent=2))
    logger.info(f"default RBAC access successfully set with role {[role]}")
    return CommandResponse.success(default_security)
