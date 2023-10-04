import json
import logging
import pathlib
from typing import Any

from click import Path, argument, command
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file, timing_decorator, wrapcontext
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@pass_azure_token("csm_api")
@argument(
    "security_file",
    type=Path(path_type=pathlib.Path),
    required=True,
)
@output_to_file
@inject_context_with_resource({'api': ['organization_id', 'url', 'workspace_id']})
def update(context: Any, azure_token: str, security_file: pathlib.Path) -> CommandResponse:
    """
    Update organization users RBAC access
    """
    organization_id = context['api_organization_id']
    api_url = context['api_url']
    work_id = context['api_workspace_id']
    details = env.fill_template(security_file)
    for item in details['acl']:
        detail = json.dumps({
            "id": item['identity_id'],
            "role": str(item.get('role')).lower() or str(details['default_role']).lower()
        })
        try:
            oauth_request(f"{api_url}/organizations/{organization_id}/workspaces/{work_id}/security/access",
                          azure_token,
                          type="POST",
                          data=detail)
        except Exception as exp:
            logger.error(exp)
            return CommandResponse.fail()
    logger.info(f"Successfully updated workspace {work_id} RBAC")
    return CommandResponse.success()
