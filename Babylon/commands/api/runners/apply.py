import json
import sys
import click

from pathlib import Path
from select import select
from logging import getLogger
from flatten_json import flatten
from click import command, option
from mako.template import Template
from Babylon.commands.api.runners.services.runner_api_svc import RunnerService
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
@option("--runner-id", "runner_id", type=str)
@option("--payload-file", "payload_file", type=Path)
@retrieve_state
def apply(state: dict, azure_token: str, organization_id: str, workspace_id: str, runner_id: str, payload_file: Path):
    data = None
    if len(select([sys.stdin], [], [], 0.0)[0]):
        stream = click.get_text_stream("stdin")
        print("reading stdin...")
        data = stream.read()
    if not data:
        if payload_file and not payload_file.exists():
            logger.error(f"{payload_file} not found")
            sys.exit(1)
        elif payload_file:
            print("reading file...")
            data = payload_file.open().read()
    result = data.replace("{{", "${").replace("}}", "}")
    t = Template(text=result, strict_undefined=True)
    vars = env.get_variables()
    flattenstate = flatten(state.get("services"), separator=".")
    payload = t.render(**vars, services=flattenstate)
    payload_json = yaml_to_json(payload)
    payload_dict: dict = json.loads(payload_json)
    service_state = state["services"]
    organization_id = payload_dict.get("organization_id") or (organization_id
                                                              or service_state["api"].get("organization_id"))
    workspace_id = payload_dict.get("workspace_id") or (workspace_id or service_state["api"].get("workspace_id"))
    runner_id = payload_dict.get("id") or (runner_id or service_state["api"].get("runner_id"))

    spec = dict()
    spec["payload"] = payload_json
    service_state["api"]["organization_id"] = organization_id
    service_state["api"]["workspace_id"] = workspace_id
    service_state["api"]["runner_id"] = runner_id
    runner_service = RunnerService(azure_token=azure_token, spec=spec, state=service_state)
    if not runner_id:
        response = runner_service.create()
        runner = response.json()
    else:
        response = runner_service.update()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = runner_service.update_security(old_security=old_security)
        response_json["security"] = security_spec
        runner = response_json
    state["services"]["api"]["dataset_id"] = runner.get("id")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    return CommandResponse.success(runner, verbose=True)
