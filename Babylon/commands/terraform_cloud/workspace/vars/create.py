import json
import logging
import pprint

import click
from click import argument
from click import command
from click import option
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPUnprocessableEntity

from .....utils.decorators import describe_dry_run
from .....utils.decorators import timing_decorator
from .....utils.environment import Environment
from .....utils.typing import QueryType
from .....utils.response import CommandResponse
from .....utils.clients import pass_tfc_client

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
@option("-w", "--workspace", "workspace_id", help="Id of the workspace to use", required=True, type=QueryType())
@describe_dry_run("Sending a variable creation payload to terraform")
@argument("var_key", type=QueryType())
@argument("var_value", type=QueryType())
@argument("var_description", type=QueryType())
@argument("var_category", type=click.Choice(['terraform', 'env'], case_sensitive=False), default='terraform')
@option("--hcl", "var_hcl", is_flag=True, help="Should the var be evaluated as a HCL string")
@option("--sensitive", "var_sensitive", is_flag=True, help="Is the var sensitive")
@timing_decorator
def create(tfc_client: TFC, workspace_id: str, var_key: str, var_value: str, var_description: str, var_category: str,
           var_hcl: bool, var_sensitive: bool) -> CommandResponse:
    """Set VAR_KEY variable to VAR_VALUE in a workspace

More information on the arguments can be found at :
https://developer.hashicorp.com/terraform/cloud-docs/api-docs/variables#request-body"""
    var_payload = {
        "data": {
            "attributes": {
                "key": var_key,
                "value": var_value,
                "description": var_description,
                "category": var_category,
                "hcl": var_hcl,
                "sensitive": var_sensitive
            }
        }
    }
    try:
        r = tfc_client.workspace_vars.create(workspace_id=workspace_id, payload=var_payload)
    except TFCHTTPUnprocessableEntity as _error:
        logger.error(f"An issue appeared while processing variable {var_key} for workspace {workspace_id}:")
        logger.error(pprint.pformat(_error.args))
        return CommandResponse.fail()
    logger.info(f"Variable {var_key} was correctly set for workspace {workspace_id}")
    logger.info(pprint.pformat(r['data']))
    return CommandResponse.success(r.get("data"))
