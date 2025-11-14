import json

from logging import getLogger
from typing import Any
from click import command, option, style, echo
from Babylon.commands.api.datasets.services.datasets_security_svc import DatasetSecurityService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import injectcontext
from Babylon.utils.decorators import retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--dataset-id", "dataset_id", type=str)
@option(
    "--role",
    "role",
    type=str,
    required=True,
    help="Role RBAC",
)
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_state
def add(state: Any,
        keycloak_token: str,
        email: str,
        organization_id: str,
        workspace_id: str,
        dataset_id: str,
        role: str = None) -> CommandResponse:
    """
    Add dataset users RBAC access
    """
    _data = [""]
    _data.append(" Add dataset users RBAC access")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["workspace_id"] = (workspace_id or service_state["api"]["workspace_id"])
    service_state["api"]["dataset_id"] = dataset_id or service_state["api"]["dataset_id"]
    service = DatasetSecurityService(keycloak_token=keycloak_token, state=service_state)
    details = json.dumps(obj={"id": email, "role": role}, indent=2, ensure_ascii=True)
    logger.info(f"Granting user {[email]} RBAC permissions on dataset {[service_state['api']['dataset_id']]}")
    response = service.add(details)
    if response is None:
        return CommandResponse.fail()
    rbac = response.json()
    logger.info(json.dumps(rbac, indent=2))
    logger.info("User RBAC permissions successfully added")
    return CommandResponse.success(rbac)
