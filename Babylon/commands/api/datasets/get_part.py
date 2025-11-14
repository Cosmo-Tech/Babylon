from logging import getLogger
from typing import Any
from click import command, option, echo, style
from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.utils.decorators import retrieve_state
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--dataset-id", "dataset_id", type=str)
@option("--dataset-part-id", "dataset_part_id", type=str)
@retrieve_state
def get_part(state: Any, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str,
             dataset_part_id: str) -> CommandResponse:
    """Get a dataset part"""
    _data = [""]
    _data.append("Get dataset part details")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or service_state["api"]["workspace_id"])
    service_state["api"]["dataset_id"] = (dataset_id or service_state["api"]["dataset_id"])
    service_state["api"]["dataset_part_id"] = (dataset_part_id or service_state["api"]["dataset_part_id"])
    service = DatasetService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"Retrieving dataset part {dataset_part_id} of dataset {[service_state['api']['dataset_id']]}")
    response = service.get_part()
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    return CommandResponse.success(dataset)
