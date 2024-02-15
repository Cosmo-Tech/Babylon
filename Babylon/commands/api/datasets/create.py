import pathlib

from logging import getLogger
from typing import Any
from click import command, argument
from click import option
from click import Path
from Babylon.commands.api.datasets.service.api import DatasetService
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
@argument(
    "payload_file",
    type=Path(path_type=pathlib.Path),
)
@retrieve_state
def create(
    state: Any,
    azure_token: str,
    organization_id: str,
    payload_file: pathlib.Path,
) -> CommandResponse:
    """
    Register new dataset
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    if not payload_file.exists():
        print(f"file {payload_file} not found in directory")
        return CommandResponse.fail()
    spec = dict()
    spec["payload"] = env.fill_template(payload_file)
    service = DatasetService(azure_token=azure_token, state=service_state, spec=spec)
    response = service.create()
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    state["services"]["api"]["dataset_id"] = dataset.get("id")
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)
    logger.info(f"Dataset '{dataset.get('id')}' successfully saved in state {state.get('id')}")
    return CommandResponse.success(dataset, verbose=True)
