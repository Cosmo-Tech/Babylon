import os
import sys
import json
import time
import pathlib
import click

from os.path import basename
from logging import getLogger
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import get_azure_token
from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService

logger = getLogger("Babylon")
env = Environment()


def deploy_dataset(namespace: str, file_content: str, deploy_dir: pathlib.Path) -> dict:
    _ret = [""]
    _ret.append("Dataset deployment")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    platform_url = env.get_ns_from_text(content=namespace)
    state = env.retrieve_state_func(state_id=env.state_id)
    state["services"]["api"]["url"] = platform_url
    state["services"]["azure"]["tenant_id"] = env.tenant_id
    azure_token = get_azure_token("csm_api")
    content = env.fill_template(data=file_content, state=state)
    payload: dict = content.get("spec").get("payload")
    sidecars = content.get("spec").get("sidecars", {})
    azure: dict = sidecars.get("azure")
    source_type = payload["sourceType"]
    dataset_id = payload.get("id")
    state["services"]["api"]["dataset_id"] = dataset_id
    spec = dict()
    if source_type == "File":
        local_path = azure["dataset"].get("file", {}).get("local_path", "")
        dataset_zip: pathlib.Path = pathlib.Path(deploy_dir) / local_path
        if not dataset_zip:
            logger.error("[api] zip archive is mandatory to create a dataset with sourceType File")
            sys.exit(1)
        elif not dataset_zip.exists():
            logger.error(f"[api] file {dataset_zip} not found in directory")
            sys.exit(1)
        elif dataset_zip.suffix != ".zip":
            logger.error("[api] file to create a dataset must be a zip")
            sys.exit(1)
    if source_type == "AzureStorage":
        if not azure.get("dataset").get("storage").get("local_path"):
            if (type(payload["source"]) is not dict or "path" not in payload["source"].keys()):
                logger.error("[api] path attribute is mandatory to create a dataset of type storage")
                sys.exit(1)
            if not payload["source"].get("name"):
                payload["source"]["name"] = state["services"]["azure"]["storage_account_name"]
            if not payload["source"].get("location"):
                payload["source"]["location"] = state["services"]["api"]["organization_id"]
        else:
            datasets_dir_path = (pathlib.Path(deploy_dir) / azure["dataset"]["storage"]["local_path"])
            files = list(pathlib.Path(datasets_dir_path).iterdir())
            datasets = list(filter(lambda x: x.suffix != "", files))
            dataset_dir_name = payload["name"].replace(" ", "_").lower()
            storage_service = DatasetStorageService(azure_token=azure_token, state=state["services"])
            for dataset in datasets:
                dataset_name = basename(dataset)
                storage_service.upload_csv_to_storage(
                    path=datasets_dir_path / f"{dataset_name}",
                    dataset_dir_name=dataset_dir_name,
                    dataset_name=dataset_name,
                    override=True,
                )
            source = dict()
            source["name"] = state["services"]["azure"]["storage_account_name"]
            source["location"] = state["services"]["api"]["organization_id"]
            source["path"] = (f"{state['services']['api']['workspace_id']}/datasets/{dataset_dir_name}")
            payload["source"] = source
    if source_type == "ADT":
        if ("source" not in payload.keys() or type(payload["source"]) is not dict
                or "location" not in payload["source"].keys()):
            logger.error("[api] location attribute is mandatory to create a dataset of type ADT")
            sys.exit(1)
    payload["main"] = True
    spec["payload"] = json.dumps(payload, indent=2, ensure_ascii=True)
    dataset_service = DatasetService(azure_token=azure_token, spec=spec, state=state["services"])
    if not state["services"]["api"]["dataset_id"]:
        response = dataset_service.create()
        if response is None:
            return str()
        dataset = response.json()
        dataset_id = dataset["id"]
        Path = (f"{state['services']['api']['workspace_id']}/datasets/{dataset_dir_name}")
        if source_type != "None":
            if source_type in ["ADT", "AzureStorage"]:
                dataset_service.refresh(dataset_id=dataset_id)
            elif source_type == "File":
                dataset_zip = pathlib.Path(azure["dataset"]["file"]["local_path"])
                dataset_service.upload(dataset_id=dataset_id, zip_file=dataset_zip)
            status = dataset_service.get_status(dataset_id=dataset_id)
            status_text = str(status.text)
            while "PENDING" in status_text:
                logger.info("[api] polling twingraph creation status...")
                time.sleep(10)
                status = dataset_service.get_status(dataset_id=dataset_id)
                status_text = str(status.text)
            if "SUCCESS" not in status_text:
                logger.error(
                    f"[api] dataset {Path}/{dataset['id']} has been created but the creation of a twingraph has failed")
            else:
                logger.info("[api] twingraph successfully created")
        logger.info(f"[api] successfully created dataset {dataset['id']}")
        if state["services"]["api"]["workspace_id"]:
            linked_dataset_response = dataset_service.link_to_workspace(dataset_id=dataset_id)
            if linked_dataset_response is None:
                logger.error(f"[api] failed to link dataset {dataset['id']}"
                             f" to workspace {state['services']['api']['workspace_id']}")
            else:
                logger.info(f"[api] dataset {dataset['id']} successfully linked "
                            f"to workspace {state['services']['api']['workspace_id']}")
    else:
        response = dataset_service.update()
        if not response:
            return str()
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
                logger.info("[api] polling twingraph status...")
                time.sleep(10)
                status = dataset_service.get_status(dataset_id=dataset_id)
                status_text = str(status.text)
            if "SUCCESS" not in status_text:
                logger.error("[api] a problem occurred while rewriting twingraph")
            else:
                logger.info("[api] twingraph successfully refreshed")
        logger.info("[api] dataset successfully updated")
    run_scripts = sidecars.get("run_scripts")
    if run_scripts:
        data = run_scripts.get("post_deploy.sh", "")
        if data:
            os.system(data)
    return dataset_id
