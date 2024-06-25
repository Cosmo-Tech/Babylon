import sys
import json
import click
import pathlib

from select import select
from logging import getLogger
from flatten_json import flatten
from click import command, option
from mako.template import Template
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.yaml_utils import yaml_to_json
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file, retrieve_state, injectcontext
from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--payload-file", "payload_file", type=pathlib.Path)
@retrieve_state
def apply(state: dict, azure_token: str, organization_id: str, payload_file: pathlib.Path):
    """Apply organization deployment"""
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
    flattenstate = flatten(state.get("services", {}), separator=".")
    payload = t.render(**vars, services=flattenstate)
    payload_json = yaml_to_json(payload)
    payload_dict: dict = json.loads(payload_json)
    service_state = state["services"]
    id = payload_dict.get("id") or (organization_id or service_state["api"].get("organization_id"))

    spec = dict()
    spec["payload"] = payload_json
    service_state["api"]["organization_id"] = id
    organization_service = OrganizationService(azure_token=azure_token, spec=spec, state=service_state)
    if not id:
        response = organization_service.create()
        if not response:
            return CommandResponse.fail()
        organization = response.json()
    else:
        response = organization_service.update()
        if not response:
            return CommandResponse.fail()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = organization_service.update_security(old_security=old_security)
        response_json["security"] = security_spec
        organization = response_json
    state["services"]["api"]["organization_id"] = organization.get("id")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    return CommandResponse.success(organization, verbose=True)
