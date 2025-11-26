import jmespath
from logging import getLogger
from typing import Any, Optional
from click import command, argument, echo, style
from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import retrieve_config_state, injectcontext
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
@retrieve_config_state
def get_all_parts(state: Any,
                  config: Any,
                  keycloak_token: str,
                  organization_id: str,
                  workspace_id: str,
                  dataset_id: str,
                  filter: Optional[str] = None) -> CommandResponse:
    """
    Get all dataset parts

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace     
       DATASET_ID: The unique identifier of the datatset
    """
    _data = [""]
    _data.append("Get all datasets part details")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = (organization_id or services_state["organization_id"])
    services_state["workspace_id"] = (workspace_id or services_state["workspace_id"])
    services_state["dataset_id"] = (dataset_id or services_state["dataset_id"])
    service = DatasetService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Getting all dataset parts from dataset {[services_state['dataset_id']]}")
    response = service.get_all_parts()
    if response is None:
        return CommandResponse.fail()
    datasets = response.json()
    if len(datasets) and filter:
        datasets = jmespath.search(filter, datasets)
    logger.info(f"Retrieved {[d.get('id') for d in datasets]} dataset parts")
    return CommandResponse.success(datasets)
