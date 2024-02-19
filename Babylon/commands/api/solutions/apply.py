import sys
import json
import yaml
import click

from pathlib import Path
from select import select
from logging import getLogger
from click import command, option
from mako.template import Template
from Babylon.utils.environment import Environment
from Babylon.utils.yaml_utils import yaml_to_json
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.commands.api.solutions.service.api import SolutionService
from Babylon.utils.decorators import output_to_file, retrieve_state, injectcontext

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@option("--payload-file", "payload_file", type=Path)
@retrieve_state
def apply(state: dict, azure_token: str, organization_id: str, solution_id: str, payload_file: Path):
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
        vars = yaml.safe_load(values_file.open())
    payload = t.render(**vars)
    payload_json = yaml_to_json(payload)
    payload_dict: dict = json.loads(payload_json)
    organization_id = payload_dict.get("organization_id") or (organization_id
                                                              or service_state["api"].get("organization_id"))
    solution_id = payload_dict.get("id") or (solution_id or service_state["api"].get("solution_id"))

    spec = dict()
    spec["payload"] = payload_json
    service_state["api"]["organization_id"] = organization_id
    service_state["api"]["solution_id"] = solution_id
    solution_service = SolutionService(azure_token=azure_token, spec=spec, state=service_state)
    if not solution_id:
        response = solution_service.create()
        solution = response.json()
    else:
        response = solution_service.update()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = solution_service.update_security(old_security=old_security)
        response_json["security"] = security_spec
        solution = response_json
    state["services"]["api"]["solution_id"] = solution.get("id")
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)
    return CommandResponse.success(solution, verbose=True)