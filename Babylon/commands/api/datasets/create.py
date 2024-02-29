import json
import sys
import time
import pathlib

from logging import getLogger
from typing import Any
from click import command, argument
from click import option
from click import Path
from Babylon.commands.api.datasets.service.api import DatasetService
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.yaml_utils import yaml_to_json

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--dataset-zip", "dataset_zip", type=Path(path_type=pathlib.Path))
@argument(
    "payload_file",
    type=Path(path_type=pathlib.Path),
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
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    if not payload_file.exists():
        print(f"file {payload_file} not found in directory")
        return CommandResponse.fail()

    file_content = payload_file.open().read()
    payload_json = yaml_to_json(file_content)
    payload_dict: dict = json.loads(payload_json)
    source_type = payload_dict.get("sourceType")

    if source_type == "File":
        if not dataset_zip:
            logger.error("Zip archive is mandatory to create a dataset with sourceType File")
            sys.exit(1)
        elif not dataset_zip.exists():
            logger.error(f"File {dataset_zip} not found in directory")
            sys.exit(1)
        elif dataset_zip.suffix != ".zip":
            logger.error("File to create a dataset must be a zip")
            sys.exit(1)

    spec = dict()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template(f.read(), state)
    service = DatasetService(azure_token=azure_token, state=service_state, spec=spec)
    response = service.create()
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    if source_type != "None":
        if source_type in ["ADT", "AzureStorage"]:
            service.refresh(dataset_id=dataset["id"])
        elif source_type == "File":
            service.upload(dataset_id=dataset["id"], zip_file=dataset_zip)

        status = service.get_status(dataset_id=dataset["id"])
        status_text = str(status.text)
        while "PENDING" in status_text:
            logger.info("Polling twingraph creation status...")
            time.sleep(10)
            status = service.get_status(dataset_id=dataset["id"])
            status_text = str(status.text)
        if "SUCCESS" not in status_text:
            logger.error(f"Dataset {dataset['id']} has been created but the creation of a twingraph has failed")
        else:
            logger.info("Twingraph successfully created")
    logger.info(f"Successfully created dataset {dataset['id']}")
    if service_state["api"]["workspace_id"]:
        linked_dataset_response = service.link_to_workspace(dataset_id=dataset['id'])
        if linked_dataset_response is None:
            logger.error(f"Failed to link dataset {dataset['id']} to workspace {service_state['api']['workspace_id']}")
        else:
            logger.error(f"Dataset {dataset['id']} successfully linked "
                         f"to workspace {service_state['api']['workspace_id']}")

    return CommandResponse.success()
