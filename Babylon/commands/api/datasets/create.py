import sys
import yaml
import time
import pathlib

from logging import getLogger
from typing import Any
from click import command, argument
from click import option
from click import Path
from Babylon.commands.api.datasets.services.api import DatasetService
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--dataset-zip", "dataset_zip", type=Path(path_type=pathlib.Path))
@argument(
    "payload_file",
    type=Path(path_type=pathlib.Path, exists=True),
)
@retrieve_state
def create(
    state: Any,
    azure_token: str,
    organization_id: str,
    workspace_id: str,
    payload_file: pathlib.Path,
    dataset_zip: pathlib.Path,
) -> CommandResponse:
    """
    Register new dataset
    """
    state['services']["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    state['services']["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    service_state = state["services"]
    file_content = payload_file.open().read()
    payload_dict: dict = yaml.safe_load(file_content)
    source_type = payload_dict.get("sourceType")
    spec = dict()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template(data=f.read(), state=state)
    service = DatasetService(azure_token=azure_token, state=service_state, spec=spec)
    response = service.create()
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    dataset_id = dataset.get('id')
    match source_type:
        case "None":
            logger.info(f"Successfully created dataset {dataset_id}")
            return CommandResponse.success(dataset, verbose=True)
        case "File":
            if not dataset_zip or not dataset_zip.exists():
                logger.error(f"File {dataset_zip} not found in directory")
                sys.exit(1)
            elif dataset_zip.suffix != ".zip":
                logger.error("File to create a dataset must be a zip")
                sys.exit(1)
            service.upload(dataset_id=dataset_id, zip_file=dataset_zip)
            when_not_none(service=service, dataset_id=dataset_id)
        case "ADT":
            service.refresh(dataset_id=dataset_id)
            when_not_none(service=service, dataset_id=dataset_id)
        case "AzureStorage":
            service.refresh(dataset_id=dataset_id)
            when_not_none(service=service, dataset_id=dataset_id)

    if state['services']["api"]["workspace_id"]:
        linked_dataset_response = service.link_to_workspace(dataset_id=dataset_id)
        if not linked_dataset_response:
            logger.error(f"Failed to link dataset {dataset_id} to workspace {state['services']['api']['workspace_id']}")
        else:
            logger.error(f"Dataset {dataset_id} successfully linked "
                         f"to workspace {state['services']['api']['workspace_id']}")
    logger.info("Twingraph successfully created")
    return CommandResponse.success(dataset, verbose=True)


def when_not_none(service: DatasetService, dataset_id: str):
    status = service.get_status(dataset_id=dataset_id)
    status_text = str(status.text)
    while "PENDING" in status_text:
        logger.info("Polling twingraph creation status...")
        time.sleep(10)
        status = service.get_status(dataset_id=dataset_id)
        status_text = str(status.text)
    if "SUCCESS" not in status_text:
        logger.error(f"Dataset {dataset_id} has been created but the creation of a twingraph has failed")
        sys.exit(1)
