import json
import pathlib
from logging import getLogger

from click import Path
from click import argument
from click import command
from click import option

from .....utils.credentials import pass_azure_token
from .....utils.decorators import output_to_file
from .....utils.decorators import require_platform_key
from .....utils.decorators import timing_decorator
from .....utils.environment import Environment
from .....utils.request import oauth_request
from .....utils.response import CommandResponse
from .....utils.typing import QueryType
from .....utils.yaml_utils import yaml_to_json

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@option("--workspace", "workspace_id", type=QueryType(), default="%deploy%workspace_id")
@argument("security_file",
          type=Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path))
@output_to_file
def update(api_url: str, azure_token: str, organization_id: str, workspace_id: str,
           security_file: pathlib.Path) -> CommandResponse:
    """
    Update workspace users RBAC access
    """
    env = Environment()
    details = env.fill_template(security_file)
    if security_file.suffix in [".yaml", ".yml"]:
        details = yaml_to_json(details)

    details = json.loads(details)
    for ele in details['acl']:
        detail = json.dumps({"id": ele['identity_id'], "role": ele.get('role') or details['default_role']})

        response = oauth_request(f"{api_url}/organizations/{organization_id}/workspaces/{workspace_id}/security/access",
                                 azure_token,
                                 type="POST",
                                 data=detail)
        if response is None:
            return CommandResponse.fail()

    logger.info(f"Successfully updated workspace {workspace_id} RBAC")
    return CommandResponse.success(details, verbose=True)
