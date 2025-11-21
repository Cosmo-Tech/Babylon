from json import dumps
from logging import getLogger

from click import command, echo, option, style

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
@option("--email", "email", type=str, required=True, help="Email valid")
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--dataset-id", "dataset_id", type=str)
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_state
def update(
    state: dict,
    keycloak_token: str,
    identity_id: str,
    email: str,
    role: str,
    organization_id: str,
    workspace_id: str,
    dataset_id: str,
) -> CommandResponse:
    """
    Update dataset users RBAC access
    """
    _data = [""]
    _data.append(" Update dataset users RBAC access")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or service_state["api"]["workspace_id"]
    service_state["api"]["dataset_id"] = dataset_id or service_state["api"]["dataset_id"]
    details = dumps({"id": email, "role": role})
    service = DatasetSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"Updating user {[email]} RBAC access in the dataset {[service_state['api']['dataset_id']]}")
    response = service.update(id=identity_id, details=details)
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info(f"User {[email]} RBAC access successfully Updated")
    return CommandResponse.success(rbacs)
