import pathlib
from logging import getLogger
from typing import Any

from click import Path, argument
from click import command
from click import option

from Babylon.commands.api.datasets.service.api import DatasetService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import (
    output_to_file,
    retrieve_state,
    timing_decorator,
    wrapcontext,
)
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--dataset-id", "dataset_id", type=str)
@argument("payload_file", type=Path(path_type=pathlib.Path))
@retrieve_state
def update(state: Any, azure_token: str, organization_id: str, dataset_id: str,
           payload_file: pathlib.Path) -> CommandResponse:
    """
    update a registered dataset
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["dataset_id"] = (dataset_id or service_state["api"]["dataset_id"])
    if not payload_file.exists():
        print(f"file {payload_file} not found in directory")
        return CommandResponse.fail()
    spec = dict()
    spec["payload"] = env.fill_template(payload_file)
    service = DatasetService(azure_token=azure_token, state=service_state, spec=spec)
    response = service.update()
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    if response:
        logger.info(f'Dataset {service_state["api"]["dataset_id"]} successfully updated')
        if service_state["api"]["dataset_id"] == state["services"]["api"]["dataset_id"]:
            logger.info(
                f'Dataset {state["services"]["api"]["dataset_id"]} stored in state has been successfully updated')
    return CommandResponse.success(dataset, verbose=True)
