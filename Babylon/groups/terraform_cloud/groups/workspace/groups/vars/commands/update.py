import json
import logging
import pprint
from typing import Optional

import click
from click import argument
from click import command
from click import option
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPUnprocessableEntity

from ..list_all_vars import list_all_vars
from ........utils import TEMPLATE_FOLDER_PATH
from ........utils.decorators import allow_dry_run
from ........utils.decorators import working_dir_requires_yaml_key

logger = logging.getLogger("Babylon")

pass_tfc = click.make_pass_decorator(TFC)


@command()
@pass_tfc
@option("-w", "--workspace", "workspace_id", help="Id of the workspace to use")
@working_dir_requires_yaml_key("terraform_workspace.yaml", "workspace_id", "workspace_id_wd")
@allow_dry_run
@argument("var_key")
@option("--value", "var_value", help="A new value to apply to the variable")
@option("--description", "var_description", help="A new description to apply to the variable")
def update(api: TFC,
           workspace_id_wd: str,
           workspace_id: Optional[str],
           var_key: str,
           var_value: Optional[str],
           var_description: Optional[str],
           dry_run: bool):
    """Update VAR_KEY variable in a workspace

More information on the arguments can be found at :
https://developer.hashicorp.com/terraform/cloud-docs/api-docs/variables#request-body"""

    workspace_id = workspace_id_wd or workspace_id

    var_payload_template = TEMPLATE_FOLDER_PATH / "terraform_cloud/var_for_workspace_create.json"
    with open(var_payload_template) as _f:
        var_payload = json.load(_f)

    if dry_run:
        original_var = var_payload['data']
        original_var['attributes']['key'] = var_key
        original_var['attributes']['value'] = "Original value"
        original_var['attributes']['description'] = "Original description"
        original_var['relationships']['workspace']['data']['id'] = workspace_id
    else:
        original_var = None
        existing_vars = list_all_vars(api, workspace_id, lookup_var_sets=False)
        for var in existing_vars:
            if var['attributes']['key'] == var_key:
                original_var = var
                break

    if not original_var:
        logger.error(f"No original value for the variable {var_key} found for workspace {workspace_id}.")
        return

    var_payload['data'] = original_var
    var_payload['data']['attributes']['value'] = var_value or original_var['attributes']['value']
    var_payload['data']['attributes']['description'] = var_description or original_var['attributes']['description']

    if dry_run:
        logger.info("DRY RUN - Sending following payload to the api")
        logger.info(pprint.pformat(var_payload))
    else:
        try:
            r = api.vars.update(variable_id=original_var['id'], payload=var_payload)
        except TFCHTTPUnprocessableEntity as _error:
            logger.error(f"An issue appeared while processing variable {var_key} for workspace {workspace_id}:")
            logger.error(pprint.pformat(_error.args))
            return
        logger.info(f"Variable {var_key} was correctly updated for workspace {workspace_id}")
        logger.info(pprint.pformat(r['data']))
