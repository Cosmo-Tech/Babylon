import sys
import json
import click
import yaml

from select import select
from pathlib import Path
from click import command, option
from logging import getLogger
from mako.template import Template
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.yaml_utils import yaml_to_json
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file, retrieve_state, injectcontext
from Babylon.services.organizations_service import OrganizationService

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--payload-file", "payload_file", type=Path)
@retrieve_state
def apply(state: dict, azure_token: str, organization_id: str, payload_file: Path):
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
    id = payload_dict.get("id") or (organization_id or service_state["api"].get("organization_id"))

    spec = dict()
    spec["payload"] = payload_json
    service_state["api"]["organization_id"] = id
    organization_service = OrganizationService(azure_token=azure_token, spec=spec, state=service_state)
    if not id:
        response = organization_service.create()
        organization = response.json()
        state["services"]["api"]["organization_id"] = organization.get("id")
        env.store_state_in_local(state)
        env.store_state_in_cloud(state)
    else:
        response = organization_service.update()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = organization_service.update_security(old_security=old_security)
        response_json["security"] = security_spec
        organization = response_json
    return CommandResponse.success(organization, verbose=True)
