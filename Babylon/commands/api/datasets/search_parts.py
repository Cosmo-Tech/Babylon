from logging import getLogger
from typing import Any

from click import argument, command, echo, style

from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_config_state
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
@argument("tag", type=str, nargs=-1)
@output_to_file
@retrieve_config_state
def search_parts(
    state: Any,
    config: Any,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    dataset_id: str,
    tag: tuple[str, ...],
) -> CommandResponse:
    """
    Get dataset part with the given tag

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
       DATASET_ID: The unique identifier of the datatset
       TAG : A specific tag used to retrieve the dataset
    """
    _data = [""]
    _data.append("Get dataset part with the given tag")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    services_state["dataset_id"] = dataset_id or services_state["dataset_id"]
    logger.info(f"Searching dataset part by tag {[tag]}")
    service = DatasetService(keycloak_token=keycloak_token, state=services_state, config=config)
    response = service.search_parts(tag=tag)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    logger.info(f"Retrieved dataset parts {[d.get('id') for d in dataset]}")
    return CommandResponse.success(dataset)
