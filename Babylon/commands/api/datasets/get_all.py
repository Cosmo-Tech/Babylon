import jmespath
import json

from logging import getLogger
from typing import Any, Optional
from click import command, option, echo, style
from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any,
            keycloak_token: str,
            organization_id: str,
            workspace_id: str,
            filter: Optional[str] = None) -> CommandResponse:
    """
    Get all datasets from the organization
    """
    _data = [""]
    _data.append("Get all datasets details")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or service_state["api"]["workspace_id"])
    service = DatasetService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"[api] Getting all datasets from organization {[service_state['api']['organization_id']]}")
    response = service.get_all()
    if response is None:
        return CommandResponse.fail()
    datasets = response.json()
    if len(datasets) and filter:
        datasets = jmespath.search(filter, datasets)
    logger.info(json.dumps(datasets, indent=2))
    return CommandResponse.success(datasets)
