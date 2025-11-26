from logging import getLogger
from typing import Any
from click import command, echo, style, argument
from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_config_state
from Babylon.utils.environment import Environment

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
@retrieve_config_state
def download_part(state: Any, config: Any, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str,
                  dataset_part_id: str) -> CommandResponse:
    """Download a dataset part

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace      
       DATASET_ID: The unique identifier of the datatset       
       DATASET_PART_ID : The unique identifier of the dataset_part_id
    """
    _data = [""]
    _data.append("Get dataset details")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = (organization_id or services_state["organization_id"])
    services_state["workspace_id"] = (workspace_id or services_state["workspace_id"])
    services_state["dataset_id"] = (dataset_id or services_state["dataset_id"])
    service = DatasetService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Downloading dataset part {dataset_part_id} from dataset {[services_state['dataset_id']]}")
    response = service.download_part(dataset_part_id=dataset_part_id)
    if response is None:
        return CommandResponse.fail()
    dataset = response.content
    with open(f"dataset_part_{dataset_part_id}", "wb") as f:
        f.write(dataset)
    logger.info(f"Dataset part {dataset_part_id} successfully saved to file dataset_part_{dataset_part_id}")
    return CommandResponse.success(dataset)
