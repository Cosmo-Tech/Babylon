import sys
import json
import time
import pathlib

from os.path import basename
from logging import getLogger

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import get_azure_token
from Babylon.commands.api.datasets.service.api import DatasetService
from Babylon.commands.api.datasets.service.storage import DatasetStorageService

logger = getLogger("Babylon")
env = Environment()


def deploy_dataset(file_content: str) -> bool:
    logger.info("Dataset deployment")
    state = env.retrieve_state_func()
    azure_token = get_azure_token("csm_api")
    ext_args = dict(azure_function_secret="")
    # state['services']["api"]["organization_id"] = "o-2v54kow7wvz6"
    service_state = state["services"]
    content = env.fill_template(data=file_content, state=state, ext_args=ext_args)
    payload: dict = content.get("spec").get("payload")
    azure: dict = content.get("spec").get("sidecars").get("azure")
    source_type = payload["sourceType"]
    dataset_id = payload.get("id")
    service_state = state["services"]
    service_state["api"]["dataset_id"] = dataset_id
    spec = dict()
    if source_type == "File":
        dataset_zip = pathlib.Path(azure["dataset"]["file"]["local_path"])
        if not dataset_zip:
            logger.error("Zip archive is mandatory to create a dataset with sourceType File")
            sys.exit(1)
        elif not dataset_zip.exists():
            logger.error(f"File {dataset_zip} not found in directory")
            sys.exit(1)
        elif dataset_zip.suffix != ".zip":
            logger.error("File to create a dataset must be a zip")
            sys.exit(1)
    if source_type == "AzureStorage":
        if not azure.get("dataset").get("storage").get("local_path"):
            if (type(payload["source"]) is not dict or "path" not in payload["source"].keys()):
                logger.error("Path attribute is mandatory to create a dataset of type storage")
                sys.exit(1)
            if not payload["source"].get("name"):
                payload["source"]["name"] = state["services"]["azure"]["storage_account_name"]
            if not payload["source"].get("location"):
                payload["source"]["location"] = state["services"]["api"]["organization_id"]
        else:
            datasets_csv_dir_path = pathlib.Path(azure["dataset"]["storage"]["local_path"])
            if datasets_csv_dir_path.is_dir():
                files = list(pathlib.Path(datasets_csv_dir_path).iterdir())
                datasets = list(filter(lambda x: x.suffix == ".csv", files))
                dataset_dir_name = payload["name"].replace(" ", "_").lower()
                storage_service = DatasetStorageService(azure_token=azure_token, state=service_state)
                for dataset in datasets:
                    dataset_name = basename(dataset)
                    storage_service.upload_csv_to_storage(
                        path=datasets_csv_dir_path / f"{dataset}",
                        dataset_dir_name=dataset_dir_name,
                        dataset_name=dataset_name,
                        override=True,
                    )
                source = dict()
                source["name"] = state["services"]["azure"]["storage_account_name"]
                source["location"] = service_state["api"]["organization_id"]
                source["path"] = f"{service_state['api']['workspace_id']}/datasets/{dataset_dir_name}"
                payload["source"] = source
    if source_type == "ADT":
        if ("source" not in payload.keys() or type(payload["source"]) is not dict
                or "location" not in payload["source"].keys()):
            logger.error("Location attribute is mandatory to create a dataset of type ADT")
            sys.exit(1)
    payload["main"] = True
    spec["payload"] = json.dumps(payload, indent=2, ensure_ascii=True)
    dataset_service = DatasetService(azure_token=azure_token, spec=spec, state=service_state)
    if not service_state["api"]["dataset_id"]:
        response = dataset_service.create()
        if response is None:
            return CommandResponse.fail()
        dataset = response.json()
        dataset_id = dataset["id"]
        if source_type != "None":
            if source_type in ["ADT", "AzureStorage"]:
                dataset_service.refresh(dataset_id=dataset_id)
            elif source_type == "File":
                dataset_zip = pathlib.Path(azure["dataset"]["file"]["local_path"])
                dataset_service.upload(dataset_id=dataset_id, zip_file=dataset_zip)
            status = dataset_service.get_status(dataset_id=dataset_id)
            status_text = str(status.text)
            while "PENDING" in status_text:
                logger.info("Polling twingraph creation status...")
                time.sleep(10)
                status = dataset_service.get_status(dataset_id=dataset_id)
                status_text = str(status.text)
            if "SUCCESS" not in status_text:
                logger.error(f"Dataset {dataset['id']} has been created but the creation of a twingraph has failed")
            else:
                logger.info("Twingraph successfully created")
        logger.info(f"Successfully created dataset {dataset['id']}")
        if service_state["api"]["workspace_id"]:
            linked_dataset_response = dataset_service.link_to_workspace(dataset_id=dataset_id)
            if linked_dataset_response is None:
                logger.error(
                    f"Failed to link dataset {dataset['id']} to workspace {service_state['api']['workspace_id']}")
            else:
                logger.info(f"Dataset {dataset['id']} successfully linked "
                            f"to workspace {service_state['api']['workspace_id']}")
    else:
        response = dataset_service.update()
        response_json = response.json()
        old_security = response_json.get("security")
        dataset_service.update_security(old_security=old_security)
        if source_type != "None":
            if source_type in ["ADT", "AzureStorage"]:
                dataset_service.refresh(dataset_id=dataset_id)
            elif source_type == "File":
                dataset_zip = pathlib.Path(azure["dataset"]["file"]["local_path"])
                dataset_service.upload(dataset_id=dataset_id, zip_file=dataset_zip)
            status = dataset_service.get_status(dataset_id=dataset_id)
            status_text = str(status.text)
            while "PENDING" in status_text:
                logger.info("Polling twingraph status...")
                time.sleep(10)
                status = dataset_service.get_status(dataset_id=dataset_id)
                status_text = str(status.text)
            if "SUCCESS" not in status_text:
                logger.error("A problem occurred while rewriting twingraph")
            else:
                logger.info("Twingraph successfully refreshed")
        logger.info("Dataset successfully updated")
    if not dataset_id:
        sys.exit(1)
