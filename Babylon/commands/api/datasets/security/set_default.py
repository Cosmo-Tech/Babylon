import json
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
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--dataset-id", "dataset_id", type=str)
@retrieve_state
def set_default(
    state: dict, keycloak_token: str, role: str, organization_id: str, workspace_id: str, dataset_id: str
) -> CommandResponse:
    """
    Set the dataset default security
    """
    _data = [""]
    _data.append(" Set dataset default security RBAC")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or service_state["api"]["workspace_id"]
    service_state["api"]["dataset_id"] = dataset_id or service_state["api"]["dataset_id"]
    details = json.dumps({"role": role})
    service = DatasetSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"[api] Setting default RBAC access to the dataset {[service_state['api']['dataset_id']]}")
    response = service.set_default(details=details)
    if response is None:
        return CommandResponse.fail()
    default_security = response.json()
    logger.info(json.dumps(default_security, indent=2))
    logger.info(f"default RBAC access successfully set with role {[role]}")
    return CommandResponse.success(default_security)
