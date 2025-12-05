from logging import getLogger
from typing import Any

from click import argument, command, echo, option, style

from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@argument("dataset_id", required=True)
@argument("dataset_part_id", required=True)
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@retrieve_state
def delete_part(
    state: Any,
    config: Any,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    dataset_id: str,
    dataset_part_id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete a dataset part

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
       DATASET_ID: The unique identifier of the datatset
       DATASET_PART_ID : The unique identifier of the dataset_part_id
    """
    _data = [""]
    _data.append("Delete a dataset part")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    service = DatasetService(keycloak_token=keycloak_token, state=services_state, config=config, dataset_id=dataset_id)
    logger.info(f"Deleting dataset part {dataset_part_id} from dataset {[dataset_id]}")
    response = service.delete_part(dataset_part_id, dataset_id, force_validation=force_validation)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Dataset part {dataset_part_id} successfully deleted")
    return CommandResponse.success(response)
