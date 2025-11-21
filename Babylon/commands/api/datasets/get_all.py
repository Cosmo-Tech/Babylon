from logging import getLogger
from typing import Any, Optional

import jmespath
from click import command, echo, option, style

from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
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
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(
    state: Any, keycloak_token: str, organization_id: str, workspace_id: str, filter: Optional[str] = None
) -> CommandResponse:
    """
    Get all datasets from the organization
    """
    _data = [""]
    _data.append("Get all datasets details")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or service_state["api"]["workspace_id"]
    service = DatasetService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"Getting all datasets from organization {[service_state['api']['organization_id']]}")
    response = service.get_all()
    if response is None:
        return CommandResponse.fail()
    datasets = response.json()
    if len(datasets) and filter:
        datasets = jmespath.search(filter, datasets)
    logger.info(f"Retrieved {[d.get('id') for d in datasets]} datasets")
    return CommandResponse.success(datasets)
