import json
import sys
from logging import getLogger
from pathlib import Path
from select import select

import click
import yaml
from click import command, option
from mako.template import Template

from Babylon.commands.api.workspaces.service.api import WorkspaceService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
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
@option("--payload-file", "payload_file", type=Path)
@retrieve_state
def apply(
    state: dict,
    azure_token: str,
    organization_id: str,
    workspace_id: str,
    payload_file: Path,
):
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
    variables_file = Path().cwd() / "variables.yaml"
    babyvars = dict()
    if variables_file.exists():
        logger.info("variables.yaml found")
        babyvars = yaml.safe_load(variables_file.open())
    payload = t.render(**babyvars)
    payload_json = yaml_to_json(payload)
    payload_dict: dict = json.loads(payload_json)
    organization_id = payload_dict.get("organization_id") or (organization_id
                                                              or service_state["api"].get("organization_id"))
    id = payload_dict.get("id") or (workspace_id or service_state["api"].get("workspace_id"))

    spec = dict()
    spec["payload"] = payload_json
    service_state["api"]["organization_id"] = organization_id
    service_state["api"]["workspace_id"] = id
    workspace_service = WorkspaceService(azure_token=azure_token, state=service_state, spec=spec)

    if not id:
        response = workspace_service.create()
        workspace = response.json()
        state["services"]["api"]["workspace_id"] = workspace.get("id")
        env.store_state_in_local(state)
        env.store_state_in_cloud(state)
    else:
        response = workspace_service.update()
        workspace = response.json()
        old_security = workspace.get("security")
        security_spec = workspace_service.update_security(old_security=old_security)
        workspace["security"] = security_spec
    return CommandResponse.success(workspace, verbose=True)
