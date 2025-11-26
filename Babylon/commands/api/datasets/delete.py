from logging import getLogger
from typing import Any
from click import command, option, echo, style, argument
from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import retrieve_config_state, injectcontext
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
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@retrieve_config_state
def delete(state: Any,
           config: Any,
           keycloak_token: str,
           organization_id: str,
           workspace_id: str,
           dataset_id: str,
           force_validation: bool = False) -> CommandResponse:
    """Delete a dataset

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace      
       DATASET_ID: The unique identifier of the datatset
    """
    _data = [""]
    _data.append("Delete a dataset")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = (organization_id or services_state["organization_id"])
    services_state["workspace_id"] = (workspace_id or services_state["workspace_id"])
    services_state["dataset_id"] = (dataset_id or services_state["dataset_id"])
    service = DatasetService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Deleting dataset {[services_state['dataset_id']]}")
    response = service.delete(force_validation=force_validation)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Dataset {[services_state['dataset_id']]} successfully deleted")
    services_state["dataset_id"] = ""
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    return CommandResponse.success(response)
