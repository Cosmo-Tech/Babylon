import logging
import pprint
from typing import Optional

from click import argument
from click import command
from click import option
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPUnprocessableEntity

from .list_all_vars import list_all_vars
from .....utils.decorators import describe_dry_run
from .....utils.decorators import timing_decorator
from .....utils.typing import QueryType
from .....utils.response import CommandResponse
from .....utils.clients import pass_tfc_client

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
@option("-w", "--workspace", "workspace_id", help="Id of the workspace to use", required=True, type=QueryType())
@describe_dry_run("Would send a variable update payload to terraform")
@argument("var_key", type=QueryType())
@option("--value", "var_value", help="A new value to apply to the variable", type=QueryType())
@option("--description", "var_description", help="A new description to apply to the variable", type=QueryType())
@timing_decorator
def update(tfc_client: TFC, workspace_id: str, var_key: str, var_value: Optional[str],
           var_description: Optional[str]) -> CommandResponse:
    """Update VAR_KEY variable in a workspace

More information on the arguments can be found at :
https://developer.hashicorp.com/terraform/cloud-docs/api-docs/variables#request-body"""

    original_var = None
    existing_vars = list_all_vars(tfc_client, workspace_id, lookup_var_sets=False)
    for var in existing_vars:
        if var['attributes']['key'] == var_key:
            original_var = var
            break

    if not original_var:
        logger.error(f"No original value for the variable {var_key} found for workspace {workspace_id}.")
        return CommandResponse.fail()

    var_payload = {"data": original_var}
    var_payload["data"]["attributes"] = {
        **var_payload["data"]["attributes"], "description": var_description,
        "value": var_value
    }

    try:
        r = tfc_client.workspace_vars.update(workspace_id=workspace_id,
                                             variable_id=original_var['id'],
                                             payload=var_payload)
    except TFCHTTPUnprocessableEntity as _error:
        logger.error(f"An issue appeared while processing variable {var_key} for workspace {workspace_id}:")
        logger.error(pprint.pformat(_error.args))
        return CommandResponse.fail()
    logger.info(f"Variable {var_key} was correctly updated for workspace {workspace_id}")
    logger.info(pprint.pformat(r['data']))
    return CommandResponse.success(r.get("data"))