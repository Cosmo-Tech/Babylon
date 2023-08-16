import json
import logging
import pprint
import pathlib

from click import Path
from click import argument
from click import command
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPUnprocessableEntity
from Babylon.utils.decorators import describe_dry_run
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_tfc_client
from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@timing_decorator
@pass_tfc_client
@describe_dry_run("Sending multiple variable creation payloads to terraform")
@argument("workspace_id", type=QueryType())
@argument("variable_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
def create_from_file(tfc_client: TFC, workspace_id: str, variable_file: pathlib.Path) -> CommandResponse:
    """
    Set multiple variables in a workspace
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
https://developer.hashicorp.com/terraform/cloud-docs/api-docs/variables#request-body
"""

    var_keys = ["key", "value", "description", "category"]
    variables = json.loads(env.fill_template(variable_file))
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
