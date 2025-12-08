from logging import getLogger
from typing import Any

from click import argument, command, echo, style

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
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@argument("dataset_id", required=True)
@argument("dataset_part_id", required=True)
@retrieve_state
def get_part(
    state: Any,
    config: Any,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    dataset_id: str,
    dataset_part_id: str,
) -> CommandResponse:
    """Get a dataset part

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
       DATASET_ID: The unique identifier of the datatset
       DATASET_PART_ID : The unique identifier of the dataset_part_id
    """
    _data = [""]
    _data.append("Get dataset part details")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    service = DatasetService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Retrieving dataset part {dataset_part_id} of dataset {[dataset_id]}")
    response = service.get_part(dataset_id)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    return CommandResponse.success(dataset)
