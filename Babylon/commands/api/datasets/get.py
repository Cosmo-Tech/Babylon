from logging import getLogger
from typing import Any
from click import command, option
from Babylon.commands.api.datasets.services.api import DatasetService
from Babylon.utils.decorators import retrieve_state
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--dataset-id", "dataset_id", type=str)
@retrieve_state
def get(state: Any, azure_token: str, organization_id: str, dataset_id: str) -> CommandResponse:
    """Get a dataset"""
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["dataset_id"] = (dataset_id or service_state["api"]["dataset_id"])
    logger.info(f"Searching dataset: {service_state['api']['dataset_id']}")
    service = DatasetService(azure_token=azure_token, state=service_state)
    response = service.get(dataset_id=dataset_id)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    return CommandResponse.success(dataset, verbose=True)
