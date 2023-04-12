import json
import logging
import pprint
import pathlib

from click import Path
from click import argument
from click import command
from click import option
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPUnprocessableEntity

from .....utils.yaml_utils import yaml_to_json

from .....utils.decorators import describe_dry_run
from .....utils.decorators import timing_decorator
from .....utils.typing import QueryType
from .....utils.response import CommandResponse
from .....utils.clients import pass_tfc_client
from .....utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
@option("-w",
        "--workspace",
        "workspace_id",
        help="Id of the workspace to use",
        default="%deploy%terraform_cloud_workspace_id",
        type=QueryType())
@describe_dry_run("Sending multiple variable creation payloads to terraform")
@argument("variable_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@timing_decorator
def create_from_file(tfc_client: TFC, workspace_id: str, variable_file: pathlib.Path) -> CommandResponse:
    """Set multiple variables in a workspace
    Variable file must be a json file containing an array of the following json objects
    [{
        "key": "",
        "value": "",
        "description": "",
        "category": "", [defaults to terraform]
        "hcl": false,
        "sensitive": false
    }]
More information on the arguments can be found at :
https://developer.hashicorp.com/terraform/cloud-docs/api-docs/variables#request-body"""

    var_keys = ["key", "value", "description", "category"]
    env = Environment()
    variables = env.fill_template(variable_file)
    if variable_file.suffix in [".yaml", ".yml"]:
        variables = yaml_to_json(variables)
    variables = json.loads(variables)
    for variable in variables:
        variable.setdefault("category", "terraform")
        variable.setdefault("hcl", False)
        variable.setdefault("sensitive", False)
        if any(key not in variable.keys() for key in var_keys):
            logger.error(f"TFC variable is missing required fields {var_keys}")
            continue
        payload = {"data": {"type": "vars", "attributes": variable}}
        try:
            tfc_client.workspace_vars.create(workspace_id=workspace_id, payload=payload)
        except TFCHTTPUnprocessableEntity as _error:
            logger.error(
                f"An issue appeared while processing variable {variable.get('key')} for workspace {workspace_id}:")
            logger.error(pprint.pformat(_error.args))
            continue
        logger.info(f"Variable {variable.get('key')} was correctly set for workspace {workspace_id}")
    return CommandResponse.success(variables)
