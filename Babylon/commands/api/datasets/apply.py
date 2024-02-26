import json
import sys
import time

import click
import yaml

from flatten_json import flatten
from logging import getLogger
from pathlib import Path
from select import select
from click import command, option
from mako.template import Template
from Babylon.commands.api.datasets.service.api import DatasetService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file, retrieve_state, injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.yaml_utils import yaml_to_json

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--dataset-id", "dataset_id", type=str)
@option("--payload-file", "payload_file", type=Path)
@option("--dataset-zip", "dataset_zip", type=Path)
@retrieve_state
def apply(
    state: dict,
    azure_token: str,
    organization_id: str,
    workspace_id: str,
    dataset_id: str,
    payload_file: Path,
    dataset_zip: Path,
):
    """Apply dataset deployment"""
    service_state = state["services"]
    data = None
    if select(
        [
            sys.stdin,
        ],
        [],
        [],
            0.0,
    )[0]:
        stream = click.get_text_stream("stdin")
        data = stream.read()
    else:
        if payload_file and not payload_file.exists():
            logger.error(f"{payload_file} not found")
            sys.exit(1)
        elif payload_file:
            data = payload_file.open().read()
    result = data.replace("{{", "${").replace("}}", "}")
    t = Template(text=result, strict_undefined=True)
    values_file = Path().cwd() / "variables.yaml"
    vars = dict()
    if values_file.exists():
        vars = yaml.safe_load(values_file.open())
    flattenstate = flatten(state.get("services"), separator=".")
    payload = t.render(**vars, services=flattenstate)
    payload_json = yaml_to_json(payload)
    payload_dict: dict = json.loads(payload_json)
    organization_id = payload_dict.get("organization_id") or (organization_id
                                                              or service_state["api"].get("organization_id"))
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])

    dataset_id = payload_dict.get("id") or (dataset_id or service_state["api"].get("dataset_id"))

    spec = dict()
    spec["payload"] = payload_json
    service_state["api"]["organization_id"] = organization_id
    service_state["api"]["dataset_id"] = dataset_id
    dataset_service = DatasetService(azure_token=azure_token, spec=spec, state=service_state)
    if not dataset_id:
        source_type = payload_dict["sourceType"]
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
        response = dataset_service.create()
        if response is None:
            return CommandResponse.fail()
        dataset = response.json()
        if source_type != "None":
            if source_type in ["ADT", "AzureStorage"]:
                dataset_service.refresh(dataset_id=dataset["id"])
            elif source_type == "File":
                dataset_service.upload(dataset_id=dataset["id"], zip_file=dataset_zip)

            status = dataset_service.get_status(dataset_id=dataset["id"])
            status_text = str(status.text)
            while "PENDING" in status_text:
                logger.info("Polling twingraph creation status...")
                time.sleep(10)
                status = dataset_service.get_status(dataset_id=dataset["id"])
                status_text = str(status.text)
            if "SUCCESS" not in status_text:
                logger.error(f"Dataset {dataset['id']} has been created but the creation of a twingraph has failed")
            else:
                logger.info("Twingraph successfully created")
        logger.info(f"Successfully created dataset {dataset['id']}")
        if service_state["api"]["workspace_id"]:
            linked_dataset_response = dataset_service.link_to_workspace(dataset_id=dataset["id"])
            if linked_dataset_response is None:
                logger.error(
                    f"Failed to link dataset {dataset['id']} to workspace {service_state['api']['workspace_id']}")
            else:
                logger.error(f"Dataset {dataset['id']} successfully linked "
                             f"to workspace {service_state['api']['workspace_id']}")

    else:
        response = dataset_service.update()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = dataset_service.update_security(old_security=old_security)
        response_json["security"] = security_spec
        dataset = response_json
    state["services"]["api"]["dataset_id"] = dataset.get("id")
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)
    return CommandResponse.success(dataset, verbose=True)
