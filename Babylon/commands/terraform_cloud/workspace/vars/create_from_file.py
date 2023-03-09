import json
import logging
import pprint
from typing import Optional
import pathlib

from click import Path
from click import argument
from click import command
from click import option
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPUnprocessableEntity

from .....utils.decorators import describe_dry_run
from .....utils.decorators import timing_decorator
from .....utils.decorators import working_dir_requires_yaml_key
from .....utils.typing import QueryType
from .....utils.response import CommandResponse
from .....utils.clients import pass_tfc_client
from .....utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
@option("-w", "--workspace", "workspace_id", help="Id of the workspace to use", type=QueryType())
@working_dir_requires_yaml_key("terraform_workspace.yaml", "workspace_id", "workspace_id_wd")
@describe_dry_run("Sending multiple variable creation payloads to terraform")
@argument("variable_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@timing_decorator
def create_from_file(tfc_client: TFC, workspace_id_wd: str, workspace_id: Optional[str],
                     variable_file: pathlib.Path) -> CommandResponse:
    """Set multiple variables in a workspace
    Variable file must be a json file containing an array of the following json objects
    [{
        "key": "",
        "value": "",
        "description": "",
        "category": "",
        "hcl": False,
        "sensitive": False
    }]
More information on the arguments can be found at :
https://developer.hashicorp.com/terraform/cloud-docs/api-docs/variables#request-body"""

    workspace_id = workspace_id_wd or workspace_id

    var_payload = {
        "data": {
            "type": "vars",
            "attributes": {
                "key": None,
                "value": None,
                "description": None,
                "category": None,
                "hcl": False,
                "sensitive": False
            }
        }
    }
    env = Environment()
    variables = json.loads(env.fill_template(variable_file))
    for variable in variables:
        if set(var_payload["data"]["attributes"].keys()) <= set(variable.keys()):
            logger.error(f"TFC variable is missing required fields {list(var_payload['data']['attributes'].keys())}")
            return CommandResponse.fail()
        payload = {"data": {"type": "vars", "attributes": variable}}
        try:
            tfc_client.workspace_vars.create(workspace_id=workspace_id, payload=payload)
        except TFCHTTPUnprocessableEntity as _error:
            logger.error(
                f"An issue appeared while processing variable {variable.get('key')} for workspace {workspace_id}:")
            logger.error(pprint.pformat(_error.args))
            return CommandResponse.fail()
        logger.info(f"Variable {variable.get('key')} was correctly set for workspace {workspace_id}")
    return CommandResponse.success(variables)
