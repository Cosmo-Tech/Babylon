from logging import getLogger
from typing import Any
from click import command
from click import argument
from Babylon.commands.api.datasets.service.api import ApiDatasetService
from Babylon.utils.decorators import retrieve_state, timing_decorator, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@pass_azure_token("csm_api")
@argument("tag", type=str)
@output_to_file
@retrieve_state
def search(state: Any, azure_token: str, tag: str) -> CommandResponse:
    """Get dataset with the given tag from the organization"""
    service_state = state["services"]
    service = ApiDatasetService(azure_token=azure_token, state=service_state)
    response = service.search(tag=tag)
    return CommandResponse.success(response, verbose=True)
