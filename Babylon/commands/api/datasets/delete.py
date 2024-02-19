from logging import getLogger
from typing import Any

from click import command
from click import option

from Babylon.commands.api.datasets.service.api import DatasetService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, timing_decorator, injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--dataset-id", "dataset_id", type=str)
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@retrieve_state
def delete(state: Any,
           azure_token: str,
           organization_id: str,
           dataset_id: str,
           force_validation: bool = False) -> CommandResponse:
    """Delete a dataset"""
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["dataset_id"] = (dataset_id or service_state["api"]["dataset_id"])
    service = DatasetService(azure_token=azure_token, state=service_state)
    logger.info(f"Deleting dataset: {service_state['api']['dataset_id']}")
    response = service.delete(force_validation=force_validation)
    if response:
        logger.info(f"Dataset '{service_state['api']['dataset_id']}' successfully deleted")
        if service_state["api"]["dataset_id"] == state["services"]["api"]["dataset_id"]:
            state["services"]["api"]["dataset_id"] = ""
            env.store_state_in_local(state)
            env.store_state_in_cloud(state)
            logger.info(
                f"Dataset '{state['services']['api']['dataset_id']}' successfully deleted from state {state.get('id')}")
    return CommandResponse.success()
