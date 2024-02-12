import pathlib

from logging import getLogger
from typing import Any
from click import Path
from click import command
from click import option
from Babylon.commands.api.datasets.service.api import ApiDatasetService
from Babylon.utils.decorators import (
    output_to_file,
    retrieve_state,
    timing_decorator,
    wrapcontext,
)
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option(
    "--payload",
    "dataset_file",
    type=Path(path_type=pathlib.Path),
    help="Your custom dataset description file (yaml or json)",
)
@retrieve_state
def update(
    state: Any,
    azure_token: str,
    dataset_file: pathlib.Path,
) -> CommandResponse:
    """
    update a registered dataset
    """
    service_state = state["services"]
    service = ApiDatasetService(azure_token=azure_token, state=service_state)
    response = service.update(dataset_file=dataset_file)
    return CommandResponse.success(response, verbose=True)
