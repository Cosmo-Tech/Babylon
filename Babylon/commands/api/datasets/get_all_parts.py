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
@option("--dataset-id", "dataset_id", type=str)
@retrieve_state
def get_all_parts(
    state: Any,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    dataset_id: str,
    filter: Optional[str] = None,
) -> CommandResponse:
    """
    Get all dataset parts
    """
    _data = [""]
    _data.append("Get all datasets part details")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or service_state["api"]["workspace_id"]
    service_state["api"]["dataset_id"] = dataset_id or service_state["api"]["dataset_id"]
    service = DatasetService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"Getting all dataset parts from dataset {[service_state['api']['dataset_id']]}")
    response = service.get_all_parts()
    if response is None:
        return CommandResponse.fail()
    datasets = response.json()
    if len(datasets) and filter:
        datasets = jmespath.search(filter, datasets)
    logger.info(f"Retrieved {[d.get('id') for d in datasets]} dataset parts")
    return CommandResponse.success(datasets)
