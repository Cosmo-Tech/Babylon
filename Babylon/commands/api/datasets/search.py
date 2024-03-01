from logging import getLogger
from typing import Any

from click import argument
from click import command, option

from Babylon.commands.api.datasets.services.api import DatasetService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file
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
@argument("tag", type=str)
@output_to_file
@retrieve_state
def search(state: Any, azure_token: str, organization_id: str, tag: str) -> CommandResponse:
    """Get dataset with the given tag from the organization"""
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    logger.info(f"Searching dataset by tag: {tag}")
    service = DatasetService(azure_token=azure_token, state=service_state)
    response = service.search(tag=tag)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    return CommandResponse.success(dataset, verbose=True)
