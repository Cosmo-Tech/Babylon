import json
import sys
from logging import getLogger
from pathlib import Path
from select import select

import click
import yaml
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
@option("--dataset-id", "dataset_id", type=str)
@option("--payload-file", "payload_file", type=Path)
@retrieve_state
def apply(state: dict, azure_token: str, organization_id: str, dataset_id: str, payload_file: Path):
    service_state = state["services"]
    data = None
    if select([
            sys.stdin,
    ], [], [], 0.0)[0]:
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
        logger.info("variables.yaml found")
        vars = yaml.safe_load(values_file.open())
    payload = t.render(**vars)
    payload_json = yaml_to_json(payload)
    payload_dict: dict = json.loads(payload_json)
    organization_id = payload_dict.get("organization_id") or (organization_id
                                                              or service_state["api"].get("organization_id"))
    dataset_id = payload_dict.get("id") or (dataset_id or service_state["api"].get("dataset_id"))

    spec = dict()
    spec["payload"] = payload_json
    service_state["api"]["organization_id"] = organization_id
    service_state["api"]["dataset_id"] = dataset_id
    dataset_service = DatasetService(azure_token=azure_token, spec=spec, state=service_state)
    if not organization_id:
        response = dataset_service.create()
        dataset = response.json()
        state["services"]["api"]["dataset_id"] = dataset.get("id")
        env.store_state_in_local(state)
        env.store_state_in_cloud(state)
    else:
        response = dataset_service.update()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = dataset_service.update_security(old_security=old_security)
        response_json["security"] = security_spec
        dataset = response_json
    return CommandResponse.success(dataset, verbose=True)
