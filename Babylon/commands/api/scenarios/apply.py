import json
import sys
import click

from pathlib import Path
from select import select
from logging import getLogger
from flatten_json import flatten
from click import command, option
from mako.template import Template
from Babylon.commands.api.scenarios.services.scenario_api_svc import ScenarioService
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
@option("--scenario-id", "scenario_id", type=str)
@option("--payload-file", "payload_file", type=Path)
@retrieve_state
def apply(state: dict, azure_token: str, organization_id: str, workspace_id: str, scenario_id: str, payload_file: Path):
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
    scenario_id = payload_dict.get("id") or (scenario_id or service_state["api"].get("scenario_id"))

    spec = dict()
    spec["payload"] = payload_json
    service_state["api"]["organization_id"] = organization_id
    service_state["api"]["workspace_id"] = workspace_id
    service_state["api"]["scenario_id"] = scenario_id
    scenario_service = ScenarioService(azure_token=azure_token, spec=spec, state=service_state)
    if not scenario_id:
        response = scenario_service.create()
        scenario = response.json()
    else:
        response = scenario_service.update()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = scenario_service.update_security(old_security=old_security)
        response_json["security"] = security_spec
        scenario = response_json
    state["services"]["api"]["dataset_id"] = scenario.get("id")
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)
    return CommandResponse.success(scenario, verbose=True)
