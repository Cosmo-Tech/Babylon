import json
import sys
import yaml
import click

from pathlib import Path
from click import command, option
from logging import getLogger
from mako.template import Template
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.yaml_utils import yaml_to_json
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.services.organizations_service import OrganizationService

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@retrieve_state
def apply(state: dict, azure_token: str, organization_id: str):
    service_state = state["services"]
    stream = click.get_text_stream("stdin")
    data = stream.read()
    if not data:
        logger.error("no data")
        sys.exit(1)
    result = data.replace("baby{{", "${").replace("}}", "}")
    t = Template(text=result, strict_undefined=True)

    cwd = Path().cwd()
    values_file = cwd / "values.yaml"
    if not values_file:
        logger.info("values.yaml not found")
        sys.exit(1)

    babyvars = yaml.safe_load(values_file.open())
    payload = t.render(**babyvars)
    payload_json = yaml_to_json(payload)
    payload_dict: dict = json.loads(payload_json)
    id = payload_dict.get("id") or (organization_id or service_state["api"].get("organization_id"))

    spec = dict()
    spec["payload"] = payload_json
    service_state["api"]["organization_id"] = id
    organization_service = OrganizationService(
        azure_token=azure_token, spec=spec, state=service_state
    )
    if not id:
        response = organization_service.create()
        organization = response.json()
    else:
        response = organization_service.update()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = organization_service.update_security(old_security=old_security)
        response_json["security"] = security_spec
        organization = response_json
    return CommandResponse.success(organization, verbose=True)
