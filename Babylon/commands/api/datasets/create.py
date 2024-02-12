import pathlib

from logging import getLogger
from typing import Any, Optional
from click import command
from click import option
from click import Path
from Babylon.commands.api.datasets.service.api import ApiDatasetService
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option(
    "--payload",
    "dataset_file",
    type=Path(path_type=pathlib.Path),
    help="Your custom dataset description file yaml",
)
@retrieve_state
def create(
    state: Any,
    azure_token: str,
    organization_id: str,
    dataset_file: Optional[pathlib.Path] = None,
) -> CommandResponse:
    """
    Register new dataset
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    service = ApiDatasetService(azure_token=azure_token, state=service_state)
    response = service.create(dataset_file=dataset_file)
    if response:
        state["services"]["api"]["dataset.id"] = response.get("id")
        env.store_state_in_local(state=state)
        env.store_state_in_cloud(state=state)
        logger.info(f"dataset id '{response.get('id')}' successfully saved in state {state.get('id')}")
    return CommandResponse.success(response, verbose=True)
