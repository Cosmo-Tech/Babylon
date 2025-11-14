from click import command, option, echo, style
from logging import getLogger
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
@pass_keycloak_token()
@output_to_file
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--dataset-id", "dataset_id", type=str)
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_state
def delete(state: dict, keycloak_token: str, email: str, organization_id: str, workspace_id: str,
           dataset_id: str) -> CommandResponse:
    """
    Delete dataset users RBAC access
    """
    _data = [""]
    _data.append(" Delete dataset users RBAC access")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["workspace_id"] = (workspace_id or service_state["api"]["workspace_id"])
    service_state["api"]["dataset_id"] = dataset_id or service_state["api"]["dataset_id"]
    service = DatasetSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"Deleting user {[email]} RBAC permissions on dataset {[service_state['api']['dataset_id']]}")
    response = service.delete(id=email)
    if response is None:
        return CommandResponse.fail()
    logger.info("User RBAC permissions successfully deleted")
    return CommandResponse.success(response)
